"""Guard: Scholarship must not carry the orphaned description_embedding column."""


def test_scholarship_has_no_orphan_description_embedding():
    from app.models.models import Scholarship

    assert "description_embedding" not in Scholarship.__table__.c
    assert "ix_scholarships_description_embedding_published" not in {
        ix.name for ix in Scholarship.__table__.indexes
    }
