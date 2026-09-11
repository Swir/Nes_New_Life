using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(EnemyHealth))]
    public sealed class BossController : MonoBehaviour
    {
        [SerializeField] private float leftX = 42f;
        [SerializeField] private float rightX = 50f;
        [SerializeField, Min(0.1f)] private float moveSpeed = 2.8f;
        [SerializeField, Min(0.1f)] private float jumpInterval = 1.7f;
        [SerializeField, Min(0.1f)] private float jumpVelocity = 10f;

        private Rigidbody2D body;
        private float timer;
        private int direction = -1;

        public void Configure(float leftBoundary, float rightBoundary)
        {
            leftX = Mathf.Min(leftBoundary, rightBoundary);
            rightX = Mathf.Max(leftBoundary, rightBoundary);
        }

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            timer = jumpInterval * 0.5f;
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

            timer -= Time.fixedDeltaTime;
            float y = body.linearVelocity.y;
            if (timer <= 0f && Mathf.Abs(y) < 0.25f)
            {
                y = jumpVelocity;
                timer = jumpInterval;
                direction *= -1;
            }

            body.linearVelocity = new Vector2(direction * moveSpeed, y);
        }
    }
}
