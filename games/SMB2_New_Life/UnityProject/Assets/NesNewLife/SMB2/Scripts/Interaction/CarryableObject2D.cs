using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    [RequireComponent(typeof(Collider2D))]
    public sealed class CarryableObject2D : MonoBehaviour
    {
        [Header("Throw Behaviour")]
        [SerializeField, Min(0f)] private float angularVelocityOnThrow = 0f;
        [SerializeField] private bool disableColliderWhileCarried = true;

        private Rigidbody2D body;
        private Collider2D objectCollider;
        private RigidbodyType2D originalBodyType;
        private Transform originalParent;
        private bool isCarried;

        public bool IsCarried => isCarried;

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
            body.linearVelocity = worldVelocity;
        }

        public void Throw(Vector2 worldVelocity)
        {
            if (!isCarried)
                return;

            ReleaseInternal();
            body.linearVelocity = worldVelocity;
            body.angularVelocity = angularVelocityOnThrow;
        }

        private void ReleaseInternal()
        {
            isCarried = false;

            transform.SetParent(originalParent, true);
            body.bodyType = originalBodyType == RigidbodyType2D.Kinematic
                ? RigidbodyType2D.Dynamic
                : originalBodyType;

            if (disableColliderWhileCarried)
                objectCollider.enabled = true;
        }
    }
}
