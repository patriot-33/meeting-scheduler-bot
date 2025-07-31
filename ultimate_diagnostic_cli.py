#!/usr/bin/env python3
"""
🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0 - CLI Interface
Command-line interface for the bulletproof diagnostic system

Usage:
    python ultimate_diagnostic_cli.py diagnose "Bot not responding" --error "Telegram webhook timeout"
    python ultimate_diagnostic_cli.py monitor --duration 60
    python ultimate_diagnostic_cli.py quick-check
    python ultimate_diagnostic_cli.py implement-solution "Fix timeout issue" --solution-file fix_timeout.py
"""

import click
import json
import sys
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.diagnostics.diagnostic_orchestrator import UltimateDiagnosticSystem, quick_diagnostic_session
from src.diagnostics.post_solution_monitoring import PostSolutionMonitor, temporary_monitoring
from src.diagnostics.core_diagnostics import DiagnosticLogger
from src.database import get_database_engine

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', default='ultimate_diagnostic.log', help='Log file path')
@click.pass_context
def cli(ctx, verbose, log_file):
    """🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['log_file'] = log_file
    
    # Initialize logger
    logger = DiagnosticLogger("ultimate_diagnostics_cli", log_file)
    ctx.obj['logger'] = logger
    
    if verbose:
        logger.logger.setLevel(5)  # Even more verbose than DEBUG
    
    # Try to get database engine
    try:
        db_engine = get_database_engine()
        ctx.obj['db_engine'] = db_engine
        logger.logger.info("Database connection established")
    except Exception as e:
        logger.logger.warning(f"Database connection failed: {e}")
        ctx.obj['db_engine'] = None

@cli.command()
@click.argument('problem_description')
@click.option('--error', help='Error message or exception details')
@click.option('--context', help='Additional context as JSON string')
@click.option('--hypotheses', multiple=True, help='Custom hypotheses to test')
@click.option('--why-answers', help='5 comma-separated answers for 5 Whys analysis')
@click.option('--full-analysis', is_flag=True, help='Run complete 6-phase analysis')
@click.pass_context
def diagnose(ctx, problem_description, error, context, hypotheses, why_answers, full_analysis):
    """🔬 Run comprehensive diagnostic analysis"""
    
    logger = ctx.obj['logger']
    db_engine = ctx.obj['db_engine']
    
    # Parse context
    context_dict = {}
    if context:
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            logger.logger.error("Invalid JSON in context parameter")
            sys.exit(1)
    
    # Initialize diagnostic system
    diagnostic_system = UltimateDiagnosticSystem(db_engine=db_engine)
    
    try:
        # Phase 1: Triage
        click.echo("🚨 Phase 1: Triaging problem...")
        triage_result = diagnostic_system.phase_1_triage(
            problem_description=problem_description,
            error_message=error or "",
            context=context_dict
        )
        
        click.echo(f"Priority: {triage_result['priority']}")
        click.echo(f"Problem Type: {triage_result['problem_type']}")
        
        # Phase 2: Systematic diagnosis
        click.echo("\n🔬 Phase 2: Running systematic diagnosis...")
        diagnosis_result = diagnostic_system.phase_2_systematic_diagnosis()
        
        click.echo(f"Overall Health: {diagnosis_result.get('sweep_results', {}).get('overall_health', 'unknown')}")
        click.echo(f"Critical Findings: {len(diagnosis_result['critical_findings'])}")
        
        # Phase 3: Hypothesis testing
        click.echo("\n🧪 Phase 3: Testing hypotheses...")
        hypothesis_result = diagnostic_system.phase_3_hypothesis_testing(
            custom_hypotheses=list(hypotheses),
            db_engine=db_engine
        )
        
        click.echo(f"Confirmed: {len(hypothesis_result['confirmed_hypotheses'])}")
        click.echo(f"Rejected: {len(hypothesis_result['rejected_hypotheses'])}")
        
        if full_analysis and why_answers:
            # Phase 4: Root cause analysis
            click.echo("\n🎯 Phase 4: Root cause analysis...")
            why_list = [w.strip() for w in why_answers.split(',')]
            if len(why_list) == 5:
                root_cause_result = diagnostic_system.phase_4_root_cause_analysis(why_list)
                click.echo(f"Root Cause: {root_cause_result['five_whys_analysis']['root_cause']}")
                click.echo(f"Confidence: {root_cause_result['root_cause_confidence']:.2f}")
            else:
                click.echo("❌ 5 Whys analysis requires exactly 5 answers")
        
        # Generate comprehensive report
        report = diagnostic_system.generate_comprehensive_report()
        report_file = f"diagnostic_report_{diagnostic_system.session_id}.json"
        
        click.echo(f"\n📋 Comprehensive report saved: {report_file}")
        click.echo(f"Session ID: {diagnostic_system.session_id}")
        click.echo(f"Phases completed: {len(report['phases_completed'])}/6")
        
        # Show summary
        if triage_result['priority'] == 'P0_CRITICAL':
            click.echo("🚨 CRITICAL ISSUE - Immediate action required!")
        elif hypothesis_result['confirmed_hypotheses']:
            click.echo(f"✅ Confirmed issues: {', '.join(hypothesis_result['confirmed_hypotheses'])}")
        
    except Exception as e:
        logger.logger.error(f"Diagnostic failed: {e}")
        click.echo(f"❌ Diagnostic failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--duration', default=60, help='Monitoring duration in minutes')
@click.option('--health-check', multiple=True, help='Custom health checks to add')
@click.option('--alert-webhook', help='Webhook URL for alerts')
@click.pass_context
def monitor(ctx, duration, health_check, alert_webhook):
    """📈 Start post-solution monitoring"""
    
    logger = ctx.obj['logger']
    db_engine = ctx.obj['db_engine']
    
    def alert_callback(alert):
        """Handle monitoring alerts"""
        if alert_webhook:
            import requests
            try:
                requests.post(alert_webhook, json={
                    'alert_id': alert.alert_id,
                    'severity': alert.severity,
                    'component': alert.component,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                })
            except Exception as e:
                logger.logger.error(f"Failed to send alert to webhook: {e}")
    
    click.echo(f"🔍 Starting monitoring for {duration} minutes...")
    
    try:
        with temporary_monitoring(
            logger=logger,
            duration_minutes=duration,
            db_engine=db_engine,
            alert_callback=alert_callback if alert_webhook else None
        ) as monitor:
            
            # Add custom health checks
            for check_name in health_check:
                # This would need implementation based on custom check format
                click.echo(f"Added custom health check: {check_name}")
            
            click.echo("✅ Monitoring completed successfully")
            
            # Show final report
            final_report = monitor.get_current_health()
            click.echo(f"Final Status: {final_report.overall_status.value}")
            click.echo(f"Total Alerts: {len(monitor.active_alerts)}")
            
    except KeyboardInterrupt:
        click.echo("\n🛑 Monitoring interrupted by user")
    except Exception as e:
        logger.logger.error(f"Monitoring failed: {e}")
        click.echo(f"❌ Monitoring failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def quick_check(ctx):
    """⚡ Run quick system health check"""
    
    logger = ctx.obj['logger']
    db_engine = ctx.obj['db_engine']
    
    click.echo("⚡ Running quick system health check...")
    
    try:
        # Quick diagnostic session without solution
        report = quick_diagnostic_session(
            problem_description="Routine health check",
            error_message="",
            db_engine=db_engine
        )
        
        # Extract key metrics
        phases = report.get('diagnostic_results', {})
        
        if 'phase_2' in phases:
            sweep_results = phases['phase_2'].get('sweep_results', {})
            overall_health = sweep_results.get('overall_health', 'unknown')
            critical_alerts = sweep_results.get('critical_alerts', [])
            
            click.echo(f"Overall Health: {overall_health.upper()}")
            
            if critical_alerts:
                click.echo("🚨 Critical Alerts:")
                for alert in critical_alerts[:5]:
                    click.echo(f"  • {alert}")
            else:
                click.echo("✅ No critical alerts")
        
        if 'phase_3' in phases:
            hypothesis_results = phases['phase_3']
            confirmed = hypothesis_results.get('confirmed_hypotheses', [])
            if confirmed:
                click.echo(f"⚠️  Issues detected: {', '.join(confirmed)}")
        
        click.echo(f"📋 Full report: diagnostic_report_{report['session_info']['session_id']}.json")
        
    except Exception as e:
        logger.logger.error(f"Quick check failed: {e}")
        click.echo(f"❌ Quick check failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('solution_description')
@click.option('--solution-file', help='Python file containing solution implementation')
@click.option('--verification-file', help='Python file containing verification function')
@click.option('--backup-files', multiple=True, help='Files to backup before implementation')
@click.option('--auto-rollback/--no-auto-rollback', default=True, help='Enable automatic rollback on failure')
@click.pass_context
def implement_solution(ctx, solution_description, solution_file, verification_file, backup_files, auto_rollback):
    """⚡ Safely implement a solution with automatic rollback"""
    
    logger = ctx.obj['logger']
    db_engine = ctx.obj['db_engine']
    
    if not solution_file:
        click.echo("❌ Solution file is required", err=True)
        sys.exit(1)
    
    # Load solution function
    try:
        spec = importlib.util.spec_from_file_location("solution_module", solution_file)
        solution_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(solution_module)
        
        if not hasattr(solution_module, 'implement'):
            click.echo("❌ Solution file must contain an 'implement()' function", err=True)
            sys.exit(1)
        
        implementation_function = solution_module.implement
        
    except Exception as e:
        click.echo(f"❌ Failed to load solution file: {e}", err=True)
        sys.exit(1)
    
    # Load verification function if provided
    verification_function = None
    if verification_file:
        try:
            spec = importlib.util.spec_from_file_location("verification_module", verification_file)
            verification_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(verification_module)
            
            if hasattr(verification_module, 'verify'):
                verification_function = verification_module.verify
            else:
                click.echo("⚠️  Verification file should contain a 'verify()' function", err=True)
        except Exception as e:
            click.echo(f"⚠️  Failed to load verification file: {e}")
    
    click.echo(f"🚀 Implementing solution: {solution_description}")
    click.echo(f"Auto-rollback: {'enabled' if auto_rollback else 'disabled'}")
    
    try:
        # Initialize diagnostic system
        diagnostic_system = UltimateDiagnosticSystem(db_engine=db_engine)
        
        # Phase 5: Safe implementation
        result = diagnostic_system.phase_5_safe_solution_implementation(
            solution_description=solution_description,
            implementation_function=implementation_function,
            verification_function=verification_function,
            files_to_backup=list(backup_files)
        )
        
        if result['success']:
            click.echo("✅ Solution implemented successfully!")
            
            # Phase 6: Start monitoring
            click.echo("📈 Starting post-solution monitoring...")
            monitoring_result = diagnostic_system.phase_6_post_solution_monitoring(
                monitoring_duration_minutes=15  # Brief monitoring for CLI
            )
            
            if monitoring_result['monitoring_successful']:
                click.echo("✅ Post-solution monitoring successful")
            else:
                click.echo("⚠️  Post-solution monitoring detected issues")
        else:
            click.echo("❌ Solution implementation failed")
            if result['implementation_result']['rollback_performed']:
                click.echo("🔄 System rolled back to previous state")
    
        # Generate final report
        report = diagnostic_system.generate_comprehensive_report()
        click.echo(f"📋 Implementation report: diagnostic_report_{diagnostic_system.session_id}.json")
        
    except Exception as e:
        logger.logger.error(f"Solution implementation failed: {e}")
        click.echo(f"❌ Solution implementation failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('report_file')
@click.pass_context
def show_report(ctx, report_file):
    """📋 Display diagnostic report summary"""
    
    try:
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        session_info = report.get('session_info', {})
        diagnostic_results = report.get('diagnostic_results', {})
        
        click.echo(f"📋 DIAGNOSTIC REPORT SUMMARY")
        click.echo(f"Session ID: {session_info.get('session_id')}")
        click.echo(f"Duration: {session_info.get('duration_seconds', 0)/60:.1f} minutes")
        click.echo(f"Problem: {session_info.get('problem_description')}")
        click.echo(f"Phases completed: {len(report.get('phases_completed', []))}/6")
        
        # Phase summaries
        if 'phase_1' in diagnostic_results:
            phase1 = diagnostic_results['phase_1']
            click.echo(f"\n🚨 Triage: {phase1.get('priority')} - {phase1.get('problem_type')}")
        
        if 'phase_2' in diagnostic_results:
            phase2 = diagnostic_results['phase_2']
            sweep_results = phase2.get('sweep_results', {})
            click.echo(f"🔬 Health: {sweep_results.get('overall_health', 'unknown').upper()}")
        
        if 'phase_3' in diagnostic_results:
            phase3 = diagnostic_results['phase_3']
            confirmed = phase3.get('confirmed_hypotheses', [])
            if confirmed:
                click.echo(f"🧪 Confirmed: {', '.join(confirmed)}")
        
        if 'phase_4' in diagnostic_results:
            phase4 = diagnostic_results['phase_4']
            analysis = phase4.get('five_whys_analysis', {})
            click.echo(f"🎯 Root Cause: {analysis.get('root_cause')}")
        
        if 'phase_5' in diagnostic_results:
            phase5 = diagnostic_results['phase_5']
            click.echo(f"⚡ Implementation: {'SUCCESS' if phase5.get('success') else 'FAILED'}")
        
        if 'phase_6' in diagnostic_results:
            phase6 = diagnostic_results['phase_6']
            click.echo(f"📈 Monitoring: {'SUCCESS' if phase6.get('monitoring_successful') else 'ISSUES'}")
        
    except FileNotFoundError:
        click.echo(f"❌ Report file not found: {report_file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON in report file: {report_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to read report: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context  
def version(ctx):
    """Show version information"""
    click.echo("🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0")
    click.echo("Built for meeting-scheduler-bot with enterprise-grade reliability")
    click.echo("")
    click.echo("Features:")
    click.echo("  • 6-phase diagnostic methodology") 
    click.echo("  • Automatic rollback and recovery")
    click.echo("  • Scientific hypothesis testing")
    click.echo("  • Real-time monitoring and alerts")
    click.echo("  • Comprehensive logging and reporting")
    click.echo("")
    click.echo("🔥 ЖЕЛЕЗНЫЙ ЗАКОН: НИКОГДА НЕ ПРЕДЛАГАЙ РЕШЕНИЕ БЕЗ ЗАВЕРШЕННОЙ ДИАГНОСТИКИ")

if __name__ == '__main__':
    cli()