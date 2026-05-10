"""
SUMO Command Builder

SUMO CLI 명령어 생성
"""

from typing import Optional


class SumoCommandBuilder:
    """
    SUMO 명령어 빌더

    SUMO CLI 실행에 필요한 명령어 및 옵션 생성
    """

    def __init__(self, sumo_binary: str = "sumo"):
        """
        Args:
            sumo_binary: SUMO 바이너리 경로
        """
        self.sumo_binary = sumo_binary

    def build_command(
        self,
        config_file: str,
        gui: bool = False,
        additional_options: Optional[dict] = None,
    ) -> list[str]:
        """
        SUMO 명령어 생성

        Args:
            config_file: .sumocfg 파일 경로
            gui: GUI 모드 사용 여부 (sumo-gui)
            additional_options: 추가 옵션 dict

        Returns:
            명령어 리스트 (subprocess에서 사용)
        """
        # 바이너리 선택
        binary = "sumo-gui" if gui else self.sumo_binary

        # 기본 명령
        cmd = [binary, "-c", config_file]

        # 추가 옵션
        if additional_options:
            for key, value in additional_options.items():
                cmd.append(f"--{key}")
                if value is not None and value != "":
                    cmd.append(str(value))

        return cmd

    def build_command_string(
        self,
        config_file: str,
        gui: bool = False,
        additional_options: Optional[dict] = None,
    ) -> str:
        """
        SUMO 명령어 문자열 생성 (로깅용)

        Args:
            config_file: .sumocfg 파일 경로
            gui: GUI 모드 사용 여부
            additional_options: 추가 옵션

        Returns:
            명령어 문자열
        """
        cmd = self.build_command(config_file, gui, additional_options)
        return " ".join(cmd)

    def get_common_options(self) -> dict:
        """
        자주 사용되는 SUMO 옵션 반환

        Returns:
            옵션 dict
        """
        return {
            "verbose": None,  # 상세 로그
            "no-step-log": None,  # 타임스텝 로그 비활성화
            "no-warnings": None,  # 경고 숨김
            "duration-log.disable": None,  # duration 로그 비활성화
            "time-to-teleport": "300",  # 텔레포트 시간
            "collision.action": "warn",  # 충돌 시 동작
        }
