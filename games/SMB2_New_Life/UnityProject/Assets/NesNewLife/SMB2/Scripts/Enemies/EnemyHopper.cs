using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class EnemyHopper : MonoBehaviour
    {
        [SerializeField, Min(0.5f)] private float jumpVelocity = 8.5f;
        [SerializeField, Min(0f)] private float horizontalSpeed = 2.2f;
        [SerializeField, Min(0.1f)] private float jumpInterval = 1.35f;
        [SerializeField] private LayerMask groundMask = ~0;

        private Rigidbody2D body;
        private Collider2D ownCollider;
        private float timer;
        private int direction = -1;

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            ownCollider = GetComponent<Collider2D>();
            timer = Random.Range(0.2f, jumpInterval);
        }

        private void FixedUpdate()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
                return;

            timer -= Time.fixedDeltaTime;
            if (timer > 0f || !IsGrounded())
                return;

            Transform player = GameManager.Instance != null ? GameManager.Instance.PlayerTransform : null;
            if (player != null)
                direction = player.position.x >= transform.position.x ? 1 : -1;

            body.linearVelocity = new Vector2(direction * horizontalSpeed, jumpVelocity);
            timer = jumpInterval;
        }

        private bool IsGrounded()
        {
            if (ownCollider == null)
                return false;

            Bounds b = ownCollider.bounds;
            Vector2 origin = new Vector2(b.center.x, b.min.y + 0.03f);
            return Physics2D.Raycast(origin, Vector2.down, 0.12f, groundMask).collider != null;
        }

        public void Configure(float jump, float horizontal, float interval, LayerMask mask)
        {
            jumpVelocity = Mathf.Max(0.5f, jump);
            horizontalSpeed = Mathf.Max(0f, horizontal);
            jumpInterval = Mathf.Max(0.1f, interval);
            groundMask = mask;
        }
    }
}
