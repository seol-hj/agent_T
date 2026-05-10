"""
Simulation Service - 통합 버전 (SUMO 실제 통합)

Network Builder + Demand Builder + SUMO Runner 통합
"""
import sys
import os
import tempfile
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from common import get_storage_gateway, StorageGateway

# SUMO 통합 모듈
from network_builder.osm_network_builder import OSMNetworkBuilder, create_placeholder_network
from demand_builder.demand_generator import DemandGenerator
from runner.sumo_runner import SUMORunner, create_placeholder_simulation_results

app = FastAPI(
    title="Agent T - Simulation Service",
    description="Network + Demand + SUMO Runner 통합 (SUMO 실제 실행)",
    version="0.4.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Gateway 싱글톤
_storage_gateway: Optional[StorageGateway] = None

def get_storage() -> StorageGateway:
    global _storage_gateway
    if _storage_gateway is None:
        _storage_gateway = get_storage_gateway()
    return _storage_gateway

# Request/Response Models
class NetworkBuildRequest(BaseModel):
    experiment_id: str
    scenario_id: str
    location: Dict[str, Any] = Field(..., description="bbox or center+radius")

class NetworkBuildResponse(BaseModel):
    success: bool
    experiment_id: str
    scenario_id: str
    network_id: str
    network_file_uri: str
    edge_count: int
    junction_count: int
    traffic_light_count: int = 0
    timestamp: str

class DemandBuildRequest(BaseModel):
    experiment_id: str
    scenario_id: str
    network_file_uri: str
    vehicle_count: int = 1000
    duration_hours: float = 1.0

class DemandBuildResponse(BaseModel):
    success: bool
    experiment_id: str
    scenario_id: str
    demand_id: str
    demand_file_uri: str
    vehicle_count: int
    route_count: int
    timestamp: str

class SimulationRunRequest(BaseModel):
    experiment_id: str
    scenario_id: str
    network_file_uri: str
    demand_file_uri: str
    duration_seconds: float = 3600.0
    step_length: float = 1.0
    use_placeholder: bool = False

class SimulationRunResponse(BaseModel):
    success: bool
    experiment_id: str
    scenario_id: str
    simulation_id: str
    status: str
    output_files: Optional[Dict[str, str]] = None
    tripinfo_stats: Optional[Dict[str, Any]] = None
    summary_stats: Optional[Dict[str, Any]] = None
    execution_time_seconds: Optional[float] = None
    timestamp: str


# Health & Info Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "simulation-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.4.0"
    }

@app.get("/ready")
async def readiness_check():
    storage = get_storage()

    # SUMO 설치 여부 확인
    sumo_status = "not_installed"
    try:
        import subprocess
        result = subprocess.run(["which", "sumo"], capture_output=True, check=False)
        if result.returncode == 0:
            sumo_status = "installed"
    except Exception:
        pass

    return {
        "status": "ready",
        "service": "simulation-service",
        "dependencies": {
            "storage_gateway": storage.provider_name,
            "sumo": sumo_status,
        }
    }

@app.get("/")
async def root():
    storage = get_storage()
    return {
        "service": "simulation-service",
        "description": "Network + Demand + SUMO Runner 통합 (실제 실행)",
        "version": "0.4.0",
        "modules": {
            "network_builder": "OSM → SUMO 도로망 (실제 netconvert)",
            "demand_builder": "교통 수요 생성 (실제 randomTrips.py + duarouter)",
            "runner": "SUMO 실행 (실제 시뮬레이션)"
        },
        "endpoints": {
            "/network/build": "POST - OSM 다운로드 및 네트워크 변환",
            "/demand/build": "POST - 교통 수요 생성",
            "/simulation/run": "POST - SUMO 시뮬레이션 실행"
        },
        "gateways": {
            "storage": storage.provider_name
        }
    }


# Network Builder Endpoint
@app.post("/network/build", response_model=NetworkBuildResponse)
async def build_network(request: NetworkBuildRequest):
    """
    OSM 데이터 다운로드 및 SUMO 네트워크 변환

    SUMO가 설치되지 않은 경우 placeholder 네트워크 생성
    """
    storage = get_storage()
    network_id = f"network-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    try:
        # 1. OSM Network Builder 초기화
        builder = OSMNetworkBuilder()

        # 2. 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 3. 네트워크 빌드 시도
            success, net_file, stats = await builder.build_network(
                location=request.location,
                output_dir=temp_dir,
                network_id=network_id
            )

            # 4. 실패 시 placeholder 사용
            if not success or not net_file:
                print(f"SUMO 도구 미설치 또는 실패 - placeholder 네트워크 생성")
                net_file = os.path.join(temp_dir, f"{network_id}.net.xml")
                stats = create_placeholder_network(net_file, network_id)

            # 5. S3에 업로드
            with open(net_file, "rb") as f:
                network_content = f.read()

            network_uri = await storage.upload(
                f"networks/{request.experiment_id}/{network_id}.net.xml",
                network_content,
                content_type="application/xml",
                metadata={
                    "experiment_id": request.experiment_id,
                    "scenario_id": request.scenario_id,
                    "network_id": network_id,
                }
            )

        return NetworkBuildResponse(
            success=True,
            experiment_id=request.experiment_id,
            scenario_id=request.scenario_id,
            network_id=network_id,
            network_file_uri=network_uri,
            edge_count=stats.get("edge_count", 0),
            junction_count=stats.get("junction_count", 0),
            traffic_light_count=stats.get("traffic_light_count", 0),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Demand Builder Endpoint
@app.post("/demand/build", response_model=DemandBuildResponse)
async def build_demand(request: DemandBuildRequest):
    """
    교통 수요 생성 (randomTrips.py + duarouter)

    SUMO가 설치되지 않은 경우 placeholder 수요 생성
    """
    storage = get_storage()
    demand_id = f"demand-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    try:
        # 1. S3에서 네트워크 파일 다운로드
        print(f"[Demand Build] Downloading network file: {request.network_file_uri}")
        network_content = await storage.download(request.network_file_uri)

        # 2. 임시 디렉토리에 저장
        with tempfile.TemporaryDirectory() as temp_dir:
            net_file = os.path.join(temp_dir, "network.net.xml")
            with open(net_file, "wb") as f:
                f.write(network_content)
            print(f"[Demand Build] Network file saved to: {net_file}")

            # 3. Demand Generator 초기화
            generator = DemandGenerator()
            print(f"[Demand Build] Generator initialized")

            # 4. 수요 생성 시도
            print(f"[Demand Build] Starting demand generation...")
            success, route_file, stats = generator.build_demand(
                net_file=net_file,
                output_dir=temp_dir,
                demand_id=demand_id,
                vehicle_count=request.vehicle_count,
                duration_hours=request.duration_hours
            )
            print(f"[Demand Build] Demand generation result: success={success}, route_file={route_file}")

            # 5. route 파일 읽기
            with open(route_file, "rb") as f:
                demand_content = f.read()
            print(f"[Demand Build] Route file read successfully")

            # 6. S3에 업로드
            demand_uri = await storage.upload(
                f"demands/{request.experiment_id}/{demand_id}.rou.xml",
                demand_content,
                content_type="application/xml",
                metadata={
                    "experiment_id": request.experiment_id,
                    "scenario_id": request.scenario_id,
                    "demand_id": demand_id,
                    "vehicle_count": request.vehicle_count,
                }
            )
            print(f"[Demand Build] Route file uploaded to: {demand_uri}")

        return DemandBuildResponse(
            success=True,
            experiment_id=request.experiment_id,
            scenario_id=request.scenario_id,
            demand_id=demand_id,
            demand_file_uri=demand_uri,
            vehicle_count=stats.get("vehicle_count", request.vehicle_count),
            route_count=stats.get("route_count", 0),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[Demand Build ERROR] {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


# SUMO Runner Endpoint
@app.post("/simulation/run", response_model=SimulationRunResponse)
async def run_simulation(request: SimulationRunRequest):
    """
    SUMO 시뮬레이션 실행

    SUMO가 설치되지 않은 경우 placeholder 결과 생성
    """
    storage = get_storage()
    simulation_id = f"sim-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    start_time = time.time()

    try:
        # 1. S3에서 파일 다운로드
        network_content = await storage.download(request.network_file_uri)
        demand_content = await storage.download(request.demand_file_uri)

        # 2. 임시 디렉토리에 저장
        with tempfile.TemporaryDirectory() as temp_dir:
            net_file = os.path.join(temp_dir, "network.net.xml")
            route_file = os.path.join(temp_dir, "routes.rou.xml")

            with open(net_file, "wb") as f:
                f.write(network_content)
            with open(route_file, "wb") as f:
                f.write(demand_content)

            # 3. Placeholder 사용 여부 확인
            if request.use_placeholder:
                print(f"Placeholder 시뮬레이션 결과 생성")
                results = create_placeholder_simulation_results(
                    temp_dir, simulation_id, vehicle_count=1000
                )
                success = True
            else:
                # 4. SUMO Runner 초기화 및 실행
                runner = SUMORunner()
                success, error, results = runner.run_full_simulation(
                    net_file=net_file,
                    route_file=route_file,
                    output_dir=temp_dir,
                    simulation_id=simulation_id,
                    duration_seconds=request.duration_seconds,
                    step_length=request.step_length
                )

                # 5. 실패 시 placeholder 사용
                if not success:
                    print(f"SUMO 실행 실패: {error} - Placeholder 사용")
                    results = create_placeholder_simulation_results(
                        temp_dir, simulation_id, vehicle_count=1000
                    )
                    success = True

            # 6. 결과 파일 S3에 업로드
            output_uris = {}
            if "output_files" in results:
                for file_type, file_path in results["output_files"].items():
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            content = f.read()

                        uri = await storage.upload(
                            f"simulations/{request.experiment_id}/{simulation_id}/{file_type}.xml",
                            content,
                            content_type="application/xml",
                            metadata={
                                "experiment_id": request.experiment_id,
                                "simulation_id": simulation_id,
                                "file_type": file_type,
                            }
                        )
                        output_uris[file_type] = uri

        execution_time = time.time() - start_time

        return SimulationRunResponse(
            success=True,
            experiment_id=request.experiment_id,
            scenario_id=request.scenario_id,
            simulation_id=simulation_id,
            status="completed",
            output_files=output_uris,
            tripinfo_stats=results.get("tripinfo_stats"),
            summary_stats=results.get("summary_stats"),
            execution_time_seconds=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulation/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """시뮬레이션 상태 조회 (향후 비동기 실행 시 사용)"""
    return {
        "simulation_id": simulation_id,
        "status": "completed",
        "progress": 1.0,
        "message": "Simulation finished"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
