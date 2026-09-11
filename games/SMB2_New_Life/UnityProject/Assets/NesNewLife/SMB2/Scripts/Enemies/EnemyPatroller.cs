using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class EnemyPatroller : MonoBehaviour
    {
        [SerializeField] private float leftX;
        [SerializeField] private float rightX;
        [SerializeField, Min(0f)] private float speed = 2.1f;

        private Rigidbody2D body;
        private int direction = -1;

        public void Configure(float leftBoundary, float rightBoundary, float moveSpeed)
        {
            leftX = Mathf.Min(leftBoundary, rightBoundary);
            rightX = Mathf.Max(leftBoundary, rightBoundary);
            speed = Mathf.Max(0f, moveSpeed);
        }

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            if (Mathf.Approximately(leftX, rightX))
            {
                leftX = transform.position.x - 2f;
                rightX = transform.position.x + 2f;
            }
        }

        private void FixedUpdate()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
            {
                body.linearVelocity = new Vector2(0f, body.linearVelocity.y);
                return;
            }

            if (transform.position.x <= leftX)
                direction = 1;
            else if (transform.position.x >= rightX)
                direction = -1;

            body.linearVelocity = new Vector2(direction * speed, body.linearVelocity.y);

            SpriteRenderer renderer = GetComponent<SpriteRenderer>();
            if (renderer != null)
                renderer.flipX = direction > 0;
        }
    }
}
