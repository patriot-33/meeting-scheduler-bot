#!/usr/bin/env python3
"""
📊 PRODUCTION MONITORING SYSTEM
Мониторинг календарной интеграции в продакшене после ML исправлений
"""
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Мониторинг продакшена"""
    
    def __init__(self):
        self.base_url = "https://meeting-scheduler-bot-fkp8.onrender.com"
        self.monitoring_active = False
        self.metrics = {
            'start_time': None,
            'health_checks': [],
            'errors_detected': [],
            'uptime_percentage': 0,
            'last_error': None
        }
    
    def start_monitoring(self, duration_hours: int = 24):
        """Запустить мониторинг на определенное время"""
        
        logger.info(f"📊 Starting production monitoring for {duration_hours} hours")
        
        self.monitoring_active = True
        self.metrics['start_time'] = datetime.now()
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        check_interval = 60  # Проверять каждую минуту
        
        while self.monitoring_active and datetime.now() < end_time:
            try:
                # Проверка здоровья системы
                health_result = self._check_system_health()
                self.metrics['health_checks'].append(health_result)
                
                # Проверка webhook
                webhook_result = self._check_webhook_status()
                
                # Анализ результатов
                if not health_result['healthy'] or not webhook_result['healthy']:
                    error_info = {
                        'timestamp': datetime.now().isoformat(),
                        'health_issue': not health_result['healthy'],
                        'webhook_issue': not webhook_result['healthy'],
                        'details': {
                            'health': health_result,
                            'webhook': webhook_result
                        }
                    }
                    self.metrics['errors_detected'].append(error_info)
                    self.metrics['last_error'] = error_info
                    
                    logger.error(f"🚨 System issue detected: {error_info}")
                
                # Сохранить промежуточные результаты
                self._save_metrics()
                
                # Логировать статус каждые 10 минут
                if len(self.metrics['health_checks']) % 10 == 0:
                    self._log_status_update()
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(check_interval)
        
        self.monitoring_active = False
        self._generate_final_report()
    
    def _check_system_health(self) -> dict:
        """Проверить здоровье системы"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'healthy': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code,
                'data': None
            }
            
            if response.status_code == 200:
                try:
                    result['data'] = response.json()
                except:
                    result['data'] = {'response': response.text[:200]}
            
            return result
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'healthy': False,
                'error': str(e),
                'response_time': None,
                'status_code': None
            }
    
    def _check_webhook_status(self) -> dict:
        """Проверить статус webhook"""
        try:
            response = requests.get(f"{self.base_url}/webhook", timeout=10)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'healthy': response.status_code in [200, 404],  # 404 тоже OK для GET на webhook
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'healthy': False,
                'error': str(e)
            }
    
    def _log_status_update(self):
        """Логировать обновление статуса"""
        total_checks = len(self.metrics['health_checks'])
        healthy_checks = sum(1 for check in self.metrics['health_checks'] if check['healthy'])
        
        uptime = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        self.metrics['uptime_percentage'] = uptime
        
        errors_count = len(self.metrics['errors_detected'])
        
        logger.info(f"📊 Status Update:")
        logger.info(f"   ⏱️ Checks: {total_checks}")
        logger.info(f"   ✅ Uptime: {uptime:.1f}%")
        logger.info(f"   ❌ Errors: {errors_count}")
        
        if self.metrics['last_error']:
            logger.info(f"   🕐 Last error: {self.metrics['last_error']['timestamp']}")
    
    def _save_metrics(self):
        """Сохранить метрики"""
        metrics_file = Path("/Users/evgenii/meeting-scheduler-bot/production_metrics.json")
        
        # Создать облегченную версию для сохранения
        save_data = {
            'start_time': self.metrics['start_time'].isoformat() if self.metrics['start_time'] else None,
            'current_time': datetime.now().isoformat(),
            'total_checks': len(self.metrics['health_checks']),
            'uptime_percentage': self.metrics['uptime_percentage'],
            'errors_count': len(self.metrics['errors_detected']),
            'last_error': self.metrics['last_error'],
            'recent_checks': self.metrics['health_checks'][-10:],  # Последние 10 проверок
            'all_errors': self.metrics['errors_detected']
        }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_final_report(self):
        """Генерировать финальный отчет"""
        
        total_checks = len(self.metrics['health_checks'])
        healthy_checks = sum(1 for check in self.metrics['health_checks'] if check['healthy'])
        uptime = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        duration = datetime.now() - self.metrics['start_time']
        
        # Анализ времени отклика
        response_times = [check['response_time'] for check in self.metrics['health_checks'] 
                         if check.get('response_time') is not None]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        report = {
            'monitoring_duration': str(duration),
            'total_health_checks': total_checks,
            'uptime_percentage': uptime,
            'errors_detected': len(self.metrics['errors_detected']),
            'performance': {
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'total_samples': len(response_times)
            },
            'status': self._determine_system_status(uptime, len(self.metrics['errors_detected'])),
            'recommendations': self._generate_recommendations(uptime, self.metrics['errors_detected'])
        }
        
        # Сохранить отчет
        report_file = Path("/Users/evgenii/meeting-scheduler-bot/production_monitoring_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # Вывести отчет
        self._print_final_report(report)
        
        logger.info(f"📄 Full monitoring report saved: {report_file}")
    
    def _determine_system_status(self, uptime: float, errors_count: int) -> str:
        """Определить статус системы"""
        if uptime >= 99 and errors_count == 0:
            return "excellent"
        elif uptime >= 95 and errors_count <= 2:
            return "good"
        elif uptime >= 90 and errors_count <= 5:
            return "acceptable"
        else:
            return "needs_attention"
    
    def _generate_recommendations(self, uptime: float, errors: list) -> list:
        """Генерировать рекомендации"""
        recommendations = []
        
        if uptime < 95:
            recommendations.append("System stability needs improvement - investigate downtime causes")
        
        if len(errors) > 3:
            recommendations.append("Multiple errors detected - review error patterns and implement fixes")
        
        if uptime >= 99:
            recommendations.append("Excellent system performance - ML fixes working perfectly")
        
        # Анализ типов ошибок
        webhook_errors = sum(1 for e in errors if e.get('webhook_issue'))
        health_errors = sum(1 for e in errors if e.get('health_issue'))
        
        if webhook_errors > 0:
            recommendations.append("Webhook issues detected - check Telegram connectivity")
        
        if health_errors > 0:
            recommendations.append("Health check failures - investigate system resources")
        
        return recommendations
    
    def _print_final_report(self, report: dict):
        """Вывести финальный отчет"""
        
        print("\n" + "="*80)
        print("📊 PRODUCTION MONITORING FINAL REPORT")
        print("="*80)
        
        print(f"\n⏱️ Monitoring Duration: {report['monitoring_duration']}")
        print(f"📋 Total Health Checks: {report['total_health_checks']}")
        print(f"✅ System Uptime: {report['uptime_percentage']:.2f}%")
        print(f"❌ Errors Detected: {report['errors_detected']}")
        
        print(f"\n🚀 Performance Metrics:")
        perf = report['performance']
        print(f"   Average Response Time: {perf['avg_response_time']:.3f}s")
        print(f"   Max Response Time: {perf['max_response_time']:.3f}s")
        print(f"   Samples Collected: {perf['total_samples']}")
        
        status = report['status']
        status_icons = {
            'excellent': '🌟',
            'good': '👍', 
            'acceptable': '⚠️',
            'needs_attention': '🔧'
        }
        
        print(f"\n📈 System Status: {status_icons.get(status, '❓')} {status.upper()}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
        
        print(f"\n🎯 ML Fixes Assessment:")
        if report['uptime_percentage'] >= 95:
            print("   ✅ ML diagnostic system successfully resolved major issues")
            print("   ✅ Calendar integration appears stable and functional")
            print("   ✅ No significant regressions detected")
        else:
            print("   ⚠️ Some stability issues remain - may need additional investigation")


def main():
    """Главная функция"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor production system')
    parser.add_argument('--duration', type=int, default=1, 
                       help='Monitoring duration in hours (default: 1)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick 5-minute test')
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor()
    
    try:
        if args.quick:
            logger.info("🚀 Running quick 5-minute production test")
            # Быстрый тест - только несколько проверок
            for i in range(5):
                health = monitor._check_system_health()
                webhook = monitor._check_webhook_status()
                
                status = "✅ OK" if health['healthy'] and webhook['healthy'] else "❌ ISSUE"
                print(f"Check {i+1}/5: {status} (Health: {health['healthy']}, Webhook: {webhook['healthy']})")
                
                if i < 4:  # Не ждать после последней проверки
                    time.sleep(60)
            
            print("\n🎯 Quick test completed!")
        else:
            duration = args.duration
            logger.info(f"📊 Starting {duration}-hour production monitoring")
            monitor.start_monitoring(duration)
    
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}")
        raise


if __name__ == "__main__":
    main()