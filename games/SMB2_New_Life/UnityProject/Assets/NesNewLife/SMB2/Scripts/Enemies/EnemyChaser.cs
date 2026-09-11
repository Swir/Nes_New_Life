using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class EnemyChaser : MonoBehaviour
    {
        [SerializeField, Min(0.1f)] private float patrolSpeed = 1.4f;
        [SerializeField, Min(0.1f)] private float chaseSpeed = 3.2f;
        [SerializeField, Min(0.5f)] private float detectionRange = 7f;
        [SerializeField] private float leftBound;
        [SerializeField] private float rightBound;

        private Rigidbody2D body;
        private int patrolDirection = 1;

        private void Awake() => body = GetComponent<Rigidbody2D>();

        private void FixedUpdate()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
                return;

            Transform player = GameManager.Instance != null ? GameManager.Instance.PlayerTransform : null;
            float velocityX;

            if (player != null && Vector2.Distance(transform.position, player.position) <= detectionRange)
            {
                velocityX = Mathf.Sign(player.position.x - transform.position.x) * chaseSpeed;
            }
            else
            {
                if (transform.position.x <= leftBound) patrolDirection = 1;
                if (transform.position.x >= rightBound) patrolDirection = -1;
                velocityX = patrolDirection * patrolSpeed;
            }

            body.linearVelocity = new Vector2(velocityX, body.linearVelocity.y);
        }

        public void Configure(float left, float right, float patrol, float chase, float range)
        {
            leftBound = Mathf.Min(left, right);
            rightBound = Mathf.Max(left, right);
            patrolSpeed = Mathf.Max(0.1f, patrol);
            chaseSpeed = Mathf.Max(patrolSpeed, chase);
            detectionRange = Mathf.Max(0.5f, range);
        }
    }
}
