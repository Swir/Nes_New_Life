using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class CameraFollow2D : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Vector2 offset = new Vector2(0f, 1f);
        [SerializeField, Min(0.01f)] private float smoothTime = 0.15f;
        [SerializeField, Min(0f)] private float horizontalLookAhead = 1.25f;
        [SerializeField] private bool lockVerticalBelowStart = true;

        private Vector3 velocity;
        private float startY;

        public Transform Target
        {
            get => target;
            set => target = value;
        }

        private void Awake()
        {
            startY = transform.position.y;
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

            if (lockVerticalBelowStart)
                desired.y = Mathf.Max(startY, desired.y);

            transform.position = Vector3.SmoothDamp(
                transform.position,
                desired,
                ref velocity,
                smoothTime
            );
        }
    }
}
