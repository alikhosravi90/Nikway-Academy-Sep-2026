import pytest

from app.master_system import (
    GuidanceDefinition,
    MasterDefinition,
    MasterRegistry,
    MasterSystemError,
    MasterVersion,
    OverrideDefinition,
    ExtensionDefinition,
    TemplateDefinition,
)


def _course_master() -> MasterDefinition:
    version = MasterVersion(
        version="1.0.0",
        schema={"title": "string", "status": "string", "modules": "array"},
        required_fields=("title", "status"),
        defaults={"status": "draft", "language": "fa"},
        allowed_states=("draft", "published"),
        overridable_paths=("status", "language"),
        extension_paths=("local_kpis", "local_sop"),
        guidance=("course-guide",),
    )
    return MasterDefinition(
        id="MASTER-COURSE-001",
        name="Course",
        object_type="course",
        current_version="1.0.0",
        versions={"1.0.0": version},
    )


def test_complete_master_template_instance_resolution_is_deterministic():
    audit = []
    registry = MasterRegistry(audit=lambda action, entity, payload: audit.append((action, entity, payload)))
    registry.register_master(_course_master())
    registry.create_template(
        TemplateDefinition(
            id="TEMPLATE-LEAN-001",
            master_id="MASTER-COURSE-001",
            master_version="1.0.0",
            name="Lean Fundamentals",
            data={"title": "Lean Fundamentals", "modules": ["basics"]},
            defaults={"status": "published"},
        )
    )
    registry.attach_guidance(
        GuidanceDefinition(
            id="course-guide",
            target_type="master",
            target_id="MASTER-COURSE-001",
            content={"definition": "A reusable learning course."},
        )
    )
    instance = registry.create_instance(
        "INSTANCE-PHARMA-001",
        "MASTER-COURSE-001",
        template_id="TEMPLATE-LEAN-001",
        overrides=(OverrideDefinition("language", "en"),),
        extensions=(ExtensionDefinition("local_kpis", ["completion_rate"]),),
    )
    first = registry.resolve_with_guidance(instance)
    second = registry.resolve_with_guidance(instance)
    assert first == second
    assert first["title"] == "Lean Fundamentals"
    assert first["status"] == "published"
    assert first["language"] == "en"
    assert first["local_kpis"] == ["completion_rate"]
    assert first["_guidance"][0]["definition"]
    assert instance.provenance.master_version == "1.0.0"
    assert instance.provenance.template_id == "TEMPLATE-LEAN-001"
    assert {item[0] for item in audit} == {
        "master_registered",
        "template_created",
        "guidance_attached",
        "instance_created",
    }


def test_undeclared_override_and_extension_are_rejected():
    registry = MasterRegistry()
    registry.register_master(_course_master())
    with pytest.raises(MasterSystemError, match="Override is not permitted"):
        registry.create_instance(
            "INSTANCE-1",
            "MASTER-COURSE-001",
            data={"title": "Course"},
            overrides=(OverrideDefinition("title", "Changed"),),
        )
    with pytest.raises(MasterSystemError, match="Extension is not permitted"):
        registry.create_instance(
            "INSTANCE-2",
            "MASTER-COURSE-001",
            data={"title": "Course"},
            extensions=(ExtensionDefinition("status", "published"),),
        )


def test_versioning_is_explicit_and_existing_instance_keeps_version():
    registry = MasterRegistry()
    registry.register_master(_course_master())
    old = registry.create_instance(
        "INSTANCE-OLD", "MASTER-COURSE-001", data={"title": "Old Course"}
    )
    registry.version_master(
        "MASTER-COURSE-001",
        MasterVersion(
            version="2.0.0",
            schema={"title": "string", "status": "string", "owner": "string"},
            required_fields=("title", "status", "owner"),
            defaults={"status": "draft"},
        ),
    )
    new = registry.create_instance(
        "INSTANCE-NEW",
        "MASTER-COURSE-001",
        data={"title": "New Course", "owner": "team"},
    )
    assert old.master_version == "1.0.0"
    assert new.master_version == "2.0.0"


@pytest.mark.parametrize(
    ("master_id", "name", "object_type", "required", "data"),
    [
        ("MASTER-FORM-001", "Form", "form", ("title",), {"title": "A3"}),
        (
            "MASTER-ORGANIZATION-001",
            "Organization",
            "organization",
            ("name",),
            {"name": "Pilot Organization"},
        ),
    ],
)
def test_representative_form_and_organization_slices(
    master_id, name, object_type, required, data
):
    registry = MasterRegistry()
    registry.register_master(
        MasterDefinition(
            id=master_id,
            name=name,
            object_type=object_type,
            current_version="1.0.0",
            versions={
                "1.0.0": MasterVersion(
                    version="1.0.0",
                    schema={key: "string" for key in required},
                    required_fields=required,
                )
            },
        )
    )
    instance = registry.create_instance("INSTANCE-" + object_type.upper(), master_id, data=data)
    assert registry.validate_instance(instance)
    assert registry.get_master(master_id).object_type == object_type
