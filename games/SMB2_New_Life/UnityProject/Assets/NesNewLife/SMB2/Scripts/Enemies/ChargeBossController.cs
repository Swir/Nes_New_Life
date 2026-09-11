using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(EnemyHealth))]
    public sealed class ChargeBossController : MonoBehaviour
    {
        [SerializeField] private float leftX = 42f;
        [SerializeField] private float rightX = 50f;
        [SerializeField, Min(0.1f)] private float patrolSpeed = 1.8f;
        [SerializeField, Min(0.1f)] private float chargeSpeed = 6.5f;
        [SerializeField, Min(0.1f)] private float chargeInterval = 2.2f;
        [SerializeField, Min(0.1f)] private float chargeSeconds = 0.8f;

        private Rigidbody2D body;
        private Transform player;
        private float intervalTimer;
        private float chargeTimer;
        private int direction = -1;
        private bool charging;

        public void Configure(float leftBoundary, float rightBoundary, float speedMultiplier = 1f)
        {
            leftX = Mathf.Min(leftBoundary, rightBoundary);
            rightX = Mathf.Max(leftBoundary, rightBoundary);
            patrolSpeed *= Mathf.Max(0.5f, speedMultiplier);
            chargeSpeed *= Mathf.Max(0.5f, speedMultiplier);
        }

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            intervalTimer = chargeInterval * 0.5f;
        }

        private void Start()
        {
            PlayerController2D controller = FindFirstObjectByType<PlayerController2D>();
            if (controller != null)
                player = controller.transform;
        }

        private void FixedUpdate()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
            {
                body.linearVelocity = Vector2.zero;
                return;
            }

            if (transform.position.x <= leftX) direction = 1;
            if (transform.position.x >= rightX) direction = -1;

            if (charging)
            {
                chargeTimer -= Time.fixedDeltaTime;
                body.linearVelocity = new Vector2(direction * chargeSpeed, body.linearVelocity.y);
                if (chargeTimer <= 0f)
                {
                    charging = false;
                    intervalTimer = chargeInterval;
                }
                return;
            }

            intervalTimer -= Time.fixedDeltaTime;
            if (intervalTimer <= 0f)
            {
                if (player != null)
                    direction = player.position.x >= transform.position.x ? 1 : -1;
                charging = true;
                chargeTimer = chargeSeconds;
                return;
            }

            body.linearVelocity = new Vector2(direction * patrolSpeed, body.linearVelocity.y);
        }
    }
}
