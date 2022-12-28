from UnityPy.classes import GameObject, Transform


def get_transform(go: GameObject) -> Transform:
    assert go.m_Transform, "GameObject has no transform"
    transform = go.m_Transform.get_obj().read()
    assert isinstance(transform, Transform), "transform is not a Transform"
    return transform
