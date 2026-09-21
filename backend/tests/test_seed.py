from sqlalchemy import func, select

from backend.app import models
from backend.app.seed import DatabaseSeeder


def count_rows(db_session, model) -> int:
    statement = select(func.count()).select_from(model)
    return db_session.scalar(statement)


def test_seeder_is_idempotent_with_existing_camera(db_session):
    db_session.add(
        models.CameraState(
            camera_id=1,
            mode="Dormant",
            fps=1,
            resolution="480p",
        )
    )
    db_session.commit()

    DatabaseSeeder(db_session).run()
    DatabaseSeeder(db_session).run()

    assert count_rows(db_session, models.OsintSource) == 4
    assert count_rows(db_session, models.CameraState) == 3
    assert count_rows(db_session, models.ThreatEvent) == 6
    assert count_rows(db_session, models.AlertLog) == 3
    assert count_rows(db_session, models.SystemLog) == 4

    existing_camera = db_session.scalar(
        select(models.CameraState).where(
            models.CameraState.camera_id == 1,
        )
    )

    assert existing_camera is not None
    assert existing_camera.mode == "Dormant"
    assert existing_camera.fps == 1
    assert existing_camera.resolution == "480p"
