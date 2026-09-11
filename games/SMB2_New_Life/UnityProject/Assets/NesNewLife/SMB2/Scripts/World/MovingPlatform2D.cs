using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class MovingPlatform2D : MonoBehaviour
    {
        [SerializeField] private Vector2 travel = new Vector2(0f, 4f);
        [SerializeField, Min(0.1f)] private float speed = 2f;

        private Rigidbody2D body;
        private Vector2 start;
        private Vector2 end;
        private bool toEnd = true;

        public void Configure(Vector2 localTravel, float moveSpeed)
        {
            travel = localTravel;
            speed = Mathf.Max(0.1f, moveSpeed);
            RecalculateEndpoints();
        }

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            RecalculateEndpoints();
        }

        private void RecalculateEndpoints()
        {
            start = transform.position;
            end = start + travel;
        }

        private void FixedUpdate()
        {
            Vector2 target = toEnd ? end : start;
            Vector2 next = Vector2.MoveTowards(body.position, target, speed * Time.fixedDeltaTime);
            body.MovePosition(next);

            if ((next - target).sqrMagnitude <= 0.0025f)
                toEnd = !toEnd;
        }
    }
}
