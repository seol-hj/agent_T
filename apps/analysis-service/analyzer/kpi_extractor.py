"""
KPI Extractor

SUMO 시뮬레이션 결과에서 KPI 추출
"""
from typing import Dict, Any, List
from lxml import etree
import io


class KPIExtractor:
    """SUMO tripinfo.xml 및 summary.xml에서 KPI 추출"""

    def extract_from_tripinfo(self, tripinfo_content: bytes) -> Dict[str, Any]:
        """
        tripinfo.xml에서 KPI 추출

        Args:
            tripinfo_content: tripinfo.xml 바이트 데이터

        Returns:
            KPI 딕셔너리
        """
        try:
            tree = etree.parse(io.BytesIO(tripinfo_content))
            root = tree.getroot()

            tripinfos = root.findall(".//tripinfo")

            if not tripinfos:
                return self._empty_tripinfo_kpis()

            # 통계 수집
            durations = []
            waiting_times = []
            time_losses = []
            route_lengths = []
            speeds = []

            for tripinfo in tripinfos:
                duration = float(tripinfo.get("duration", 0))
                waiting_time = float(tripinfo.get("waitingTime", 0))
                time_loss = float(tripinfo.get("timeLoss", 0))
                route_length = float(tripinfo.get("routeLength", 0))

                # 평균 속도 계산 (m/s)
                if duration > 0:
                    avg_speed = route_length / duration
                else:
                    avg_speed = 0.0

                durations.append(duration)
                waiting_times.append(waiting_time)
                time_losses.append(time_loss)
                route_lengths.append(route_length)
                speeds.append(avg_speed)

            total_trips = len(tripinfos)

            return {
                "completed_trips": total_trips,
                "avg_travel_time": sum(durations) / total_trips if total_trips > 0 else 0.0,
                "avg_waiting_time": sum(waiting_times) / total_trips if total_trips > 0 else 0.0,
                "avg_time_loss": sum(time_losses) / total_trips if total_trips > 0 else 0.0,
                "avg_route_length": sum(route_lengths) / total_trips if total_trips > 0 else 0.0,
                "avg_speed": sum(speeds) / total_trips if total_trips > 0 else 0.0,
                "total_waiting_time": sum(waiting_times),
                "total_time_loss": sum(time_losses),
                "total_distance": sum(route_lengths),
            }

        except Exception as e:
            print(f"tripinfo KPI 추출 실패: {e}")
            return self._empty_tripinfo_kpis()

    def extract_from_summary(self, summary_content: bytes) -> Dict[str, Any]:
        """
        summary.xml에서 KPI 추출

        Args:
            summary_content: summary.xml 바이트 데이터

        Returns:
            KPI 딕셔너리
        """
        try:
            tree = etree.parse(io.BytesIO(summary_content))
            root = tree.getroot()

            steps = root.findall(".//step")

            if not steps:
                return self._empty_summary_kpis()

            # 시간별 통계 수집
            vehicles_running = []
            mean_speeds = []
            vehicles_loaded = []
            vehicles_inserted = []
            vehicles_ended = []

            for step in steps:
                running = int(step.get("running", 0))
                speed = float(step.get("meanSpeed", 0))
                loaded = int(step.get("loaded", 0))
                inserted = int(step.get("inserted", 0))
                ended = int(step.get("ended", 0))

                vehicles_running.append(running)
                mean_speeds.append(speed)
                vehicles_loaded.append(loaded)
                vehicles_inserted.append(inserted)
                vehicles_ended.append(ended)

            total_steps = len(steps)

            return {
                "total_steps": total_steps,
                "total_loaded": max(vehicles_loaded) if vehicles_loaded else 0,
                "total_inserted": sum(vehicles_inserted),
                "total_ended": sum(vehicles_ended),
                "avg_vehicles_running": sum(vehicles_running) / total_steps if total_steps > 0 else 0.0,
                "max_vehicles_running": max(vehicles_running) if vehicles_running else 0,
                "avg_mean_speed": sum(mean_speeds) / total_steps if total_steps > 0 else 0.0,
                "peak_hour_vehicles": max(vehicles_running) if vehicles_running else 0,
            }

        except Exception as e:
            print(f"summary KPI 추출 실패: {e}")
            return self._empty_summary_kpis()

    def extract_all_kpis(
        self,
        tripinfo_content: bytes,
        summary_content: bytes
    ) -> Dict[str, Any]:
        """
        모든 KPI 추출 및 통합

        Args:
            tripinfo_content: tripinfo.xml 바이트 데이터
            summary_content: summary.xml 바이트 데이터

        Returns:
            통합 KPI 딕셔너리
        """
        tripinfo_kpis = self.extract_from_tripinfo(tripinfo_content)
        summary_kpis = self.extract_from_summary(summary_content)

        # 추가 계산 지표
        derived_kpis = {}

        # 처리율 (throughput)
        if summary_kpis["total_loaded"] > 0:
            derived_kpis["completion_rate"] = (
                summary_kpis["total_ended"] / summary_kpis["total_loaded"]
            )
        else:
            derived_kpis["completion_rate"] = 0.0

        # 혼잡도 지표 (waiting time / travel time)
        if tripinfo_kpis["avg_travel_time"] > 0:
            derived_kpis["congestion_index"] = (
                tripinfo_kpis["avg_waiting_time"] / tripinfo_kpis["avg_travel_time"]
            )
        else:
            derived_kpis["congestion_index"] = 0.0

        # km/h로 변환
        derived_kpis["avg_speed_kmh"] = tripinfo_kpis["avg_speed"] * 3.6
        derived_kpis["avg_mean_speed_kmh"] = summary_kpis["avg_mean_speed"] * 3.6

        return {
            "tripinfo": tripinfo_kpis,
            "summary": summary_kpis,
            "derived": derived_kpis,
        }

    def _empty_tripinfo_kpis(self) -> Dict[str, Any]:
        """빈 tripinfo KPI"""
        return {
            "completed_trips": 0,
            "avg_travel_time": 0.0,
            "avg_waiting_time": 0.0,
            "avg_time_loss": 0.0,
            "avg_route_length": 0.0,
            "avg_speed": 0.0,
            "total_waiting_time": 0.0,
            "total_time_loss": 0.0,
            "total_distance": 0.0,
        }

    def _empty_summary_kpis(self) -> Dict[str, Any]:
        """빈 summary KPI"""
        return {
            "total_steps": 0,
            "total_loaded": 0,
            "total_inserted": 0,
            "total_ended": 0,
            "avg_vehicles_running": 0.0,
            "max_vehicles_running": 0,
            "avg_mean_speed": 0.0,
            "peak_hour_vehicles": 0,
        }

    def generate_summary_report(self, kpis: Dict[str, Any]) -> str:
        """
        KPI 요약 리포트 생성 (텍스트)

        Args:
            kpis: extract_all_kpis 결과

        Returns:
            마크다운 형식 리포트
        """
        tripinfo = kpis.get("tripinfo", {})
        summary = kpis.get("summary", {})
        derived = kpis.get("derived", {})

        report = f"""# 시뮬레이션 KPI 리포트

## 통행 통계
- **완료된 통행**: {tripinfo.get('completed_trips', 0)}건
- **평균 통행 시간**: {tripinfo.get('avg_travel_time', 0):.2f}초
- **평균 대기 시간**: {tripinfo.get('avg_waiting_time', 0):.2f}초
- **평균 시간 손실**: {tripinfo.get('avg_time_loss', 0):.2f}초
- **평균 통행 거리**: {tripinfo.get('avg_route_length', 0):.2f}m
- **평균 속도**: {derived.get('avg_speed_kmh', 0):.2f} km/h

## 시스템 통계
- **총 시뮬레이션 스텝**: {summary.get('total_steps', 0)}
- **생성된 차량 수**: {summary.get('total_loaded', 0)}대
- **완료된 차량 수**: {summary.get('total_ended', 0)}대
- **평균 운행 차량 수**: {summary.get('avg_vehicles_running', 0):.2f}대
- **최대 운행 차량 수**: {summary.get('max_vehicles_running', 0)}대
- **평균 평균 속도**: {derived.get('avg_mean_speed_kmh', 0):.2f} km/h

## 성능 지표
- **완료율**: {derived.get('completion_rate', 0) * 100:.2f}%
- **혼잡도 지수**: {derived.get('congestion_index', 0):.4f}
- **총 대기 시간**: {tripinfo.get('total_waiting_time', 0):.2f}초
- **총 시간 손실**: {tripinfo.get('total_time_loss', 0):.2f}초
- **총 주행 거리**: {tripinfo.get('total_distance', 0):.2f}m
"""
        return report
