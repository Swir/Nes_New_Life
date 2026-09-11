using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(PlayerController2D))]
    public sealed class CarrySystem2D : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private Transform pickupPoint;
        [SerializeField] private Transform carryAnchor;
        [SerializeField] private LayerMask carryableMask;

        [Header("Pickup")]
        [SerializeField, Min(0.05f)] private float pickupRadius = 0.45f;
        [SerializeField] private KeyCode actionKey = KeyCode.LeftShift;
        [SerializeField] private KeyCode alternateActionKey = KeyCode.RightShift;

        [Header("Throw")]
        [SerializeField, Min(0f)] private float throwHorizontalSpeed = 9f;
        [SerializeField] private float throwVerticalSpeed = 2.5f;
        [SerializeField, Min(0f)] private float dropForwardSpeed = 1.25f;

        private PlayerController2D player;
        private CarryableObject2D carriedObject;

        public bool IsCarrying => carriedObject != null;
        public CarryableObject2D CarriedObject => carriedObject;

        private void Awake()
        {
            player = GetComponent<PlayerController2D>();
        }

        private void Update()
        {
            if (!ActionPressedThisFrame())
                return;

            if (carriedObject != null)
            {
                ThrowCurrent();
                return;
            }

            TryPickupNearest();
        }

        private bool ActionPressedThisFrame()
        {
            return Input.GetKeyDown(actionKey) || Input.GetKeyDown(alternateActionKey);
        }

        private void TryPickupNearest()
        {
            if (pickupPoint == null || carryAnchor == null)
                return;

            Collider2D[] hits = Physics2D.OverlapCircleAll(
                pickupPoint.position,
                pickupRadius,
                carryableMask
            );

            CarryableObject2D best = null;
            float bestDistanceSquared = float.PositiveInfinity;

            foreach (Collider2D hit in hits)
            {
                CarryableObject2D candidate = hit.GetComponentInParent<CarryableObject2D>();
                if (candidate == null || candidate.IsCarried)
                    continue;

                float distanceSquared = (candidate.transform.position - pickupPoint.position).sqrMagnitude;
                if (distanceSquared >= bestDistanceSquared)
                    continue;

                best = candidate;
                bestDistanceSquared = distanceSquared;
            }

            if (best != null && best.TryPickup(carryAnchor))
                carriedObject = best;
        }

        public void ThrowCurrent()
        {
            if (carriedObject == null)
                return;

            Vector2 velocity = new Vector2(
                player.FacingSign * throwHorizontalSpeed,
                throwVerticalSpeed
            );

            CarryableObject2D released = carriedObject;
            carriedObject = null;
            released.Throw(velocity);
        }

        public void DropCurrent()
        {
            if (carriedObject == null)
                return;

            Vector2 velocity = new Vector2(
                player.FacingSign * dropForwardSpeed,
                0f
            );

            CarryableObject2D released = carriedObject;
            carriedObject = null;
            released.Drop(velocity);
        }

        private void OnDisable()
        {
            if (carriedObject != null)
                DropCurrent();
        }

        private void OnDrawGizmosSelected()
        {
            if (pickupPoint == null)
                return;

            Gizmos.DrawWireSphere(pickupPoint.position, pickupRadius);
        }
    }
}
