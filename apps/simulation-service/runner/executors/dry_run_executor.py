"""
Dry Run SUMO Executor

모의 실행 Executor (테스트 및 초기 개발용)
"""

import time
import os
from pathlib import Path

from .executor import SumoExecutor, ExecutionResult


class DryRunSumoExecutor(SumoExecutor):
    """
    Dry Run SUMO Executor

    실제 SUMO를 실행하지 않고 더미 출력 파일 생성
    """

    def __init__(self, simulate_delay: bool = True):
        """
        Args:
            simulate_delay: 실행 시간 지연 시뮬레이션 여부
        """
        self.simulate_delay = simulate_delay

    async def execute(
        self,
        config_file_path: str,
        working_directory: str,
    ) -> ExecutionResult:
        """모의 SUMO 실행"""
        start_time = time.time()

        # 시뮬레이션 지연 (옵션)
        if self.simulate_delay:
            await self._simulate_execution()

        # 더미 출력 파일 생성
        output_files = self._create_dummy_outputs(working_directory)

        execution_time_ms = (time.time() - start_time) * 1000

        return ExecutionResult(
            success=True,
            return_code=0,
            stdout="[DRY RUN] SUMO simulation completed successfully (simulated)",
            stderr="",
            execution_time_ms=execution_time_ms,
            output_files=output_files,
        )

    def validate_environment(self) -> tuple[bool, str]:
        """환경 검증 (항상 성공)"""
        return True, "Dry run mode - no SUMO installation required"

    async def _simulate_execution(self):
        """실행 시간 시뮬레이션 (비동기)"""
        import asyncio
        await asyncio.sleep(0.1)  # 100ms 지연

    def _create_dummy_outputs(self, working_directory: str) -> dict[str, str]:
        """
        더미 출력 파일 생성

        Args:
            working_directory: 작업 디렉토리

        Returns:
            {output_type: file_path}
        """
        work_dir = Path(working_directory)
        work_dir.mkdir(parents=True, exist_ok=True)

        output_files = {}

        # tripinfo.xml
        tripinfo_path = work_dir / "tripinfo.xml"
        tripinfo_path.write_text(self._generate_dummy_tripinfo())
        output_files["tripinfo"] = str(tripinfo_path)

        # summary.xml
        summary_path = work_dir / "summary.xml"
        summary_path.write_text(self._generate_dummy_summary())
        output_files["summary"] = str(summary_path)

        # queue.xml
        queue_path = work_dir / "queue.xml"
        queue_path.write_text(self._generate_dummy_queue())
        output_files["queue"] = str(queue_path)

        # emission.xml
        emission_path = work_dir / "emission.xml"
        emission_path.write_text(self._generate_dummy_emission())
        output_files["emission"] = str(emission_path)

        return output_files

    def _generate_dummy_tripinfo(self) -> str:
        """더미 tripinfo.xml 생성"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<tripinfos xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tripinfo id="veh_0" depart="0.00" departLane="e_0_0" departPos="5.10" departSpeed="0.00"
              departDelay="0.00" arrival="120.00" arrivalLane="e_1_0" arrivalPos="95.50"
              arrivalSpeed="13.89" duration="120.00" routeLength="500.00" waitingTime="10.00"
              waitingCount="2" stopTime="0.00" timeLoss="15.50" rerouteNo="0"
              devices="tripinfo" vType="passenger" speedFactor="1.00" vaporized=""/>
    <tripinfo id="veh_1" depart="10.00" departLane="e_1_0" departPos="5.10" departSpeed="0.00"
              departDelay="0.00" arrival="135.00" arrivalLane="e_2_0" arrivalPos="95.50"
              arrivalSpeed="13.89" duration="125.00" routeLength="520.00" waitingTime="12.00"
              waitingCount="3" stopTime="0.00" timeLoss="18.20" rerouteNo="0"
              devices="tripinfo" vType="passenger" speedFactor="1.00" vaporized=""/>
</tripinfos>
"""

    def _generate_dummy_summary(self) -> str:
        """더미 summary.xml 생성"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<summary xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <step time="0.00" loaded="10" inserted="10" running="10" waiting="0" ended="0"
          meanWaitingTime="0.00" meanTravelTime="0.00" meanSpeed="10.50" meanSpeedRelative="0.75"
          duration="0" halting="2" vaporized="0"/>
    <step time="60.00" loaded="20" inserted="18" running="18" waiting="2" ended="2"
          meanWaitingTime="5.50" meanTravelTime="120.00" meanSpeed="12.30" meanSpeedRelative="0.88"
          duration="60000" halting="3" vaporized="0"/>
    <step time="120.00" loaded="30" inserted="28" running="26" waiting="2" ended="4"
          meanWaitingTime="6.20" meanTravelTime="118.50" meanSpeed="13.10" meanSpeedRelative="0.94"
          duration="120000" halting="2" vaporized="0"/>
</summary>
"""

    def _generate_dummy_queue(self) -> str:
        """더미 queue.xml 생성"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<queue-export xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <data timestep="0.00">
        <edge id="e_0" queueing_time="0.00" queueing_length="0.00" queueing_length_ahead_of_traffic_light="0.00"/>
        <edge id="e_1" queueing_time="0.00" queueing_length="0.00" queueing_length_ahead_of_traffic_light="0.00"/>
    </data>
    <data timestep="60.00">
        <edge id="e_0" queueing_time="15.50" queueing_length="25.00" queueing_length_ahead_of_traffic_light="20.00"/>
        <edge id="e_1" queueing_time="10.20" queueing_length="18.00" queueing_length_ahead_of_traffic_light="15.00"/>
    </data>
</queue-export>
"""

    def _generate_dummy_emission(self) -> str:
        """더미 emission.xml 생성"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<emission-export xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <timestep time="0.00">
        <vehicle id="veh_0" eclass="HBEFA3/PC_G_EU4" CO2="2640.00" CO="164.80" HC="0.81"
                 NOx="0.51" PMx="0.06" fuel="1137.48" electricity="0.00" noise="68.24"/>
    </timestep>
    <timestep time="60.00">
        <vehicle id="veh_0" eclass="HBEFA3/PC_G_EU4" CO2="2850.00" CO="178.20" HC="0.88"
                 NOx="0.55" PMx="0.07" fuel="1228.91" electricity="0.00" noise="69.15"/>
        <vehicle id="veh_1" eclass="HBEFA3/PC_G_EU4" CO2="2720.00" CO="170.50" HC="0.84"
                 NOx="0.53" PMx="0.06" fuel="1172.34" electricity="0.00" noise="68.78"/>
    </timestep>
</emission-export>
"""
