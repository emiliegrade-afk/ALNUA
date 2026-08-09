"""Shared imports for split API routers."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
import re
import subprocess
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import sentry_sdk
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents.accountant_agent import AccountantAgent
from agents.ai_programmer_agent import AiProgrammerAgent
from agents.analyst_business_agent import BusinessAnalystAgent
from agents.analyst_data_agent import DataAnalystAgent
from agents.ads_agent import AdsAgent
from agents.brainstorm_agent import BrainstormAgent, BRAINSTORM_NOTES_ROOT, WELCOME_MESSAGE
from agents.content_agent import ContentAgent
from agents.controller_agent import ControllerAgent
from agents.coo_agent import COOAgent
from agents.dev_backend_agent import DevBackendAgent
from agents.dev_app_agent import DevAppAgent
from agents.dev_gaming_agent import DevGamingAgent
from agents.electronics_agent import ElectronicsAgent
from agents.embedded_dev_agent import EmbeddedDevAgent
from agents.environment_artist_agent import EnvironmentArtistAgent
from agents.firmware_agent import FirmwareAgent
from agents.hardware_agent import HardwareAgent
from agents.industrial_design_agent import IndustrialDesignAgent
from agents.level_designer_agent import LevelDesignerAgent
from agents.marketing_agent import MarketingAgent
from agents.mechanical_agent import MechanicalAgent
from agents.narrative_designer_agent import NarrativeDesignerAgent
from agents.pm_agent import PMAgent
from agents.qa_agent import QAAgent
from agents.qa_gaming_agent import QaGamingAgent
from agents.qa_robot_agent import QaRobotAgent
from agents.safety_agent import SafetyAgent
from agents.secretary_agent import SecretaryAgent
from agents.simulation_agent import SimulationAgent
from agents.sound_designer_agent import SoundDesignerAgent
from agents.spec_agent import SpecAgent
from agents.technical_artist_agent import TechnicalArtistAgent
from agents.vfx_artist_agent import VfxArtistAgent
from agents.vision_ai_agent import VisionAiAgent
from api.analytics_helpers import (
    filter_by_date_range,
    latest_values_by_project,
    month_bounds,
    parse_period,
    pct_change,
    previous_month_bounds,
    sum_metric_in_range,
)
from bots.sav_bot import SAVBot
from bots.telegram_bot import get_telegram_bot
from bots.reviews_bot import ReviewsBot
from bots.publisher_bot import PublisherBot
from bots.analytics_bot import AnalyticsBot
from config.paths import data_dir, get_hub_repo_path
from config.settings import get_settings
from database.supabase_client import get_supabase
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from services.beta_portal import (
    create_feedback_ticket,
    create_tester_token,
    decode_tester_token,
    get_tester_or_404,
    invite_url_for_slug,
    latest_app_version,
    project_slug_for,
    resolve_project_by_slug,
    upload_screenshot,
)
from services.brand_schemas import BrandAnalysis, BrandElement
from services.brand_storage import BRAND_KITS_ROOT, ensure_brand_kit_dirs
from services.briefing_generator import (
    generate_and_store_daily_briefing,
    get_briefing_for_date,
)
from services.eve_bom import (
    BOM_CATEGORIES,
    BOM_STATUSES,
    bom_totals,
    create_bom_item,
    delete_bom_item,
    list_bom_items,
    update_bom_item,
)
from services.kit_generator import ALL_FORMAT_NAMES, generate_full_kit
from services.palette import extract_kmeans_colors, merge_palettes
from services.report_generator import REPORT_FILENAME, generate_brand_report
from services.release_generator import generate_release_notes
from services.segmentation import generate_isolated_assets, segment_elements
from services.vision_llm import analyze_brand_image, prepare_brand_image
from services.partnerships import (
    AFFILIATE_FALLBACK_URL,
    CONTRACTS_ROOT,
    affiliate_link_timeline,
    affiliate_public_url,
    build_contract_path,
    ensure_contract_dirs,
    generate_affiliate_code,
    open_contract_file,
    open_contracts_folder,
    parse_audience_size_text,
    partnership_stats,
    record_affiliate_click,
    record_affiliate_conversion,
    run_partnership_followup_reminders,
)
from services.waitlist import (
    compute_position,
    generate_waitlist_email,
    markdown_to_html,
    waitlist_stats,
    waitlist_url_for_slug,
)
from services.competition import (
    add_points,
    get_leaderboard,
    get_scores,
    get_team_leaderboard,
    check_and_archive_if_new_month,
    POINT_VALUES,
)
from services.finance_agent import (
    attach_project_names,
    build_dashboard,
    fetch_transactions as fetch_finance_transactions,
    generate_monthly_summary,
    get_or_generate_summary,
)
from skills.skill_gh_issues import (
    get_issue,
    get_open_prs,
    list_ready_issues,
    poll_issues_loop,
)
from skills.skill_langfuse import agent_trace
from services.facades.costs_facade import get_daily_costs, get_monthly_costs, get_weekly_costs

from api.middleware import hub_api_key_valid
from api.schemas import *  # noqa: F403
from api.schemas import beta_tester_auth
from api.state import (
    accept_authenticated_websocket,
    get_coo_agent,
    ws_manager,
)

logger = logging.getLogger(__name__)

from fastapi import APIRouter
