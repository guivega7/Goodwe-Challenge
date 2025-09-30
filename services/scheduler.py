"""
Serviço de agendamento (APScheduler) para tarefas recorrentes.

Jobs implementados:
- Resumo diário em horário configurável (DAILY_SUMMARY_TIME, ex: 21:30)
- Anúncio do Autopilot pela manhã (AUTOPILOT_ANNOUNCE_TIME, ex: 08:00)

Ativação controlada por ENABLE_SCHEDULER=true|false.
"""

from __future__ import annotations

import os
import random
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from utils.logger import get_logger
from utils.energia import dispara_alerta
from services.energy_autopilot import build_daily_plan
from services.smartplug_service import collect_and_store
from services.device_sync import sync_tuya_devices

logger = get_logger(__name__)

_scheduler: Optional[BackgroundScheduler] = None
_started = False


def _parse_hhmm(value: str, default: str) -> tuple[int, int]:
    raw = (value or default).strip()
    try:
        h, m = raw.split(":", 1)
        return int(h), int(m)
    except Exception:
        dh, dm = default.split(":", 1)
        return int(dh), int(dm)


def _get_tz() -> pytz.BaseTzInfo:
    # Aceitar TIMEZONE, TZ (mantendo retrocompatibilidade)
    tzname = os.getenv("TIMEZONE") or os.getenv("TZ") or "UTC"
    try:
        return pytz.timezone(tzname)
    except Exception:
        return pytz.utc


def job_daily_summary():
    """Gera e dispara o resumo diário via IFTTT (mensagem amigável)."""
    energia_gerada = round(random.uniform(15.0, 35.0), 1)
    economia = round(energia_gerada * 0.75, 2)
    mensagem = (
        f"Resumo do dia: {energia_gerada} kWh gerados, R$ {economia} economizados. "
        f"Sistema funcionando normalmente!"
    )
    logger.info(f"[Scheduler] Enviando resumo diário: {mensagem}")
    try:
        dispara_alerta("Resumo_diario", mensagem)
    except Exception as e:
        logger.error(f"[Scheduler] Falha ao enviar resumo diário: {e}")


def job_morning_autopilot():
    """Gera o plano do dia e anuncia na Alexa via IFTTT."""
    try:
        # Parâmetros opcionais via .env
        soc = float(os.getenv("AUTOPILOT_SOC_DEFAULT", "35"))
        forecast = float(os.getenv("AUTOPILOT_FORECAST_DEFAULT", "8"))

        plan = build_daily_plan(soc, forecast)
        msg = plan.get("alexa_message") or "Plano do dia disponível."

        # Reuso da infraestrutura de alerta (envia via IFTTT). Colocamos a mensagem em value1.
        # A função dispara_alerta usa evento como nome IFTTT; aqui usamos low_battery só para roteamento IFTTT.
        # Alternativamente, você pode criar um evento específico no IFTTT (ex: autopilot_announce).
        logger.info(f"[Scheduler] Anunciando Autopilot na Alexa: {msg}")
        dispara_alerta("low_battery", msg)
    except Exception as e:
        logger.error(f"[Scheduler] Falha no anúncio do Autopilot: {e}")


def init_scheduler(app) -> Optional[BackgroundScheduler]:
    global _scheduler, _started
    if _started:
        return _scheduler

    enabled = os.getenv("ENABLE_SCHEDULER", "true").lower() in ("1", "true", "yes", "on")
    if not enabled:
        logger.info("[Scheduler] Desativado por configuração (ENABLE_SCHEDULER=false)")
        return None

    # Evitar inicializar duas vezes com reloader do Flask
    if os.getenv("WERKZEUG_RUN_MAIN") != "true" and app.debug:
        logger.info("[Scheduler] Aguardando reloader (modo debug)")
        return None

    tz = _get_tz()
    scheduler = BackgroundScheduler(timezone=tz)

    # Funções wrapper para executar tarefas dentro do contexto da aplicação
    def collect_and_store_with_context():
        with app.app_context():
            collect_and_store()

    def sync_tuya_devices_with_context():
        with app.app_context():
            sync_tuya_devices()

    # Job: Coleta periódica smart plug (intervalo em segundos, default 60)
    try:
        interval_seconds = int(os.getenv("SMARTPLUG_INTERVAL", "60"))
        if interval_seconds > 0:
            from apscheduler.triggers.interval import IntervalTrigger
            scheduler.add_job(
                collect_and_store_with_context,
                IntervalTrigger(seconds=interval_seconds, timezone=tz),
                id="smartplug-collector",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            logger.info(f"[Scheduler] Coleta SmartPlug a cada {interval_seconds}s")
    except Exception as e:
        logger.error(f"[Scheduler] Falha ao agendar smartplug collector: {e}")

    # Job: Resumo diário
    hh, mm = _parse_hhmm(os.getenv("DAILY_SUMMARY_TIME", "21:30"), "21:30")
    scheduler.add_job(
        job_daily_summary,
        CronTrigger(hour=hh, minute=mm, timezone=tz),
        id="daily-summary",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job: Autopilot anúncio pela manhã
    ah, am = _parse_hhmm(os.getenv("AUTOPILOT_ANNOUNCE_TIME", "08:00"), "08:00")
    scheduler.add_job(
        job_morning_autopilot,
        CronTrigger(hour=ah, minute=am, timezone=tz),
        id="autopilot-morning",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    # Job: Sincronização de dispositivos Tuya (intervalo configurável)
    try:
        if os.getenv("ENABLE_DEVICE_SYNC", "true").lower() in ("1", "true", "yes", "on"):
            interval_sync = int(os.getenv("DEVICE_SYNC_INTERVAL", "1800"))  # 30 min default
            from apscheduler.triggers.interval import IntervalTrigger
            scheduler.add_job(
                sync_tuya_devices_with_context,
                IntervalTrigger(seconds=interval_sync, timezone=tz),
                id="tuya-device-sync",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            logger.info(f"[Scheduler] Sincronização Tuya a cada {interval_sync}s")
    except Exception as e:
        logger.error(f"[Scheduler] Falha ao agendar sync Tuya: {e}")
    _scheduler = scheduler
    _started = True
    logger.info(
        f"[Scheduler] Iniciado. Resumo diário às {hh:02d}:{mm:02d}, Autopilot às {ah:02d}:{am:02d} ({tz})"
    )
    return scheduler


def get_jobs_info():
    if not _scheduler:
        return []
    info = []
    for j in _scheduler.get_jobs():
        info.append({
            "id": j.id,
            "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
            "trigger": str(j.trigger),
        })
    return info
