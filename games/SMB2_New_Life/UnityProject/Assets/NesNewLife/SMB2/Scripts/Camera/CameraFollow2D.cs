using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Camera))]
    public sealed class CameraFollow2D : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Vector2 offset = new Vector2(0f, 1f);
        [SerializeField, Min(0.01f)] private float smoothTime = 0.15f;
        [SerializeField, Min(0f)] private float horizontalLookAhead = 1.25f;
        [SerializeField] private bool lockVerticalBelowStart = true;

        private Vector3 velocity;
        private float startY;
        private Camera cameraComponent;
        private bool useWorldBounds;
        private Rect worldBounds;

        public Transform Target
        {
            get => target;
            set => target = value;
        }

        private void Awake()
        {
            cameraComponent = GetComponent<Camera>();
            startY = transform.position.y;
        }

        public void SetWorldBounds(Rect bounds)
        {
            worldBounds = bounds;
            useWorldBounds = bounds.width > 0.01f && bounds.height > 0.01f;
            velocity = Vector3.zero;
        }

        public void ClearWorldBounds()
        {
            useWorldBounds = false;
            velocity = Vector3.zero;
        }

        private void LateUpdate()
        {
            if (target == null)
                return;

            int facingSign = 0;
            PlayerController2D controller = target.GetComponent<PlayerController2D>();
            if (controller != null)
                facingSign = controller.FacingSign;

            Vector3 desired = new Vector3(
                target.position.x + offset.x + horizontalLookAhead * facingSign,
                target.position.y + offset.y,
                transform.position.z
            );

            if (lockVerticalBelowStart && !useWorldBounds)
                desired.y = Mathf.Max(startY, desired.y);

            if (useWorldBounds)
                desired = ClampToBounds(desired);

            transform.position = Vector3.SmoothDamp(
                transform.position,
                desired,
                ref velocity,
                smoothTime
            );
        }

        private Vector3 ClampToBounds(Vector3 desired)
        {
            float halfHeight = cameraComponent.orthographicSize;
            float halfWidth = halfHeight * cameraComponent.aspect;

            float minX = worldBounds.xMin + halfWidth;
            float maxX = worldBounds.xMax - halfWidth;
            float minY = worldBounds.yMin + halfHeight;
            float maxY = worldBounds.yMax - halfHeight;

            desired.x = minX <= maxX
                ? Mathf.Clamp(desired.x, minX, maxX)
                : worldBounds.center.x;

            desired.y = minY <= maxY
                ? Mathf.Clamp(desired.y, minY, maxY)
                : worldBounds.center.y;

            return desired;
        }
    }
}
