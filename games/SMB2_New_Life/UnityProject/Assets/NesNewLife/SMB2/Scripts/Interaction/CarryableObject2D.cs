using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(Collider2D))]
    public sealed class CarryableObject2D : MonoBehaviour
    {
        [Header("Throw Behaviour")]
        [SerializeField, Min(0f)] private float angularVelocityOnThrow = 120f;
        [SerializeField] private bool disableColliderWhileCarried = true;
        [SerializeField, Min(1)] private int thrownDamage = 1;

        private Rigidbody2D body;
        private Collider2D objectCollider;
        private RigidbodyType2D originalBodyType;
        private Transform originalParent;
        private bool isCarried;
        private bool isThrown;

        public bool IsCarried => isCarried;
        public bool IsThrown => isThrown;

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            objectCollider = GetComponent<Collider2D>();
            originalBodyType = body.bodyType;
            originalParent = transform.parent;
        }

        public bool TryPickup(Transform carryAnchor)
        {
            if (isCarried || carryAnchor == null)
                return false;

            isCarried = true;
            isThrown = false;
            body.linearVelocity = Vector2.zero;
            body.angularVelocity = 0f;
            body.bodyType = RigidbodyType2D.Kinematic;

            if (disableColliderWhileCarried)
                objectCollider.enabled = false;

            transform.SetParent(carryAnchor, true);
            transform.localPosition = Vector3.zero;
            transform.localRotation = Quaternion.identity;
            return true;
        }

        public void Drop(Vector2 worldVelocity)
        {
            if (!isCarried)
                return;

            ReleaseInternal();
            isThrown = false;
            body.linearVelocity = worldVelocity;
        }

        public void Throw(Vector2 worldVelocity)
        {
            if (!isCarried)
                return;

            ReleaseInternal();
            isThrown = true;
            body.linearVelocity = worldVelocity;
            body.angularVelocity = angularVelocityOnThrow;
        }

        private void OnCollisionEnter2D(Collision2D collision)
        {
            if (!isThrown)
                return;

            EnemyHealth enemy = collision.collider.GetComponentInParent<EnemyHealth>();
            if (enemy == null)
                return;

            enemy.Damage(thrownDamage);

            BossController boss = collision.collider.GetComponentInParent<BossController>();
            if (boss != null)
            {
                isThrown = false;
                body.angularVelocity = 0f;
                body.linearVelocity = new Vector2(-body.linearVelocity.x * 0.25f, 2.5f);
                return;
            }

            Destroy(gameObject);
        }

        private void ReleaseInternal()
        {
            isCarried = false;
            transform.SetParent(originalParent, true);
            body.bodyType = originalBodyType == RigidbodyType2D.Kinematic ? RigidbodyType2D.Dynamic : originalBodyType;

            if (disableColliderWhileCarried)
                objectCollider.enabled = true;
        }
    }
}
