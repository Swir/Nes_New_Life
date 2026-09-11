using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    public sealed class PullablePlant : MonoBehaviour
    {
        [SerializeField] private CarryableObject2D buriedItem;
        private bool pulled;

        public bool IsPulled => pulled;

        public void Configure(CarryableObject2D item)
        {
            buriedItem = item;
            if (buriedItem != null)
                buriedItem.gameObject.SetActive(false);
        }

        public bool TryPull(Transform carryAnchor, out CarryableObject2D item)
        {
            item = null;
            if (pulled || buriedItem == null || carryAnchor == null)
                return false;

            pulled = true;
            buriedItem.gameObject.SetActive(true);
            buriedItem.transform.position = transform.position + Vector3.up * 0.45f;

            if (!buriedItem.TryPickup(carryAnchor))
            {
                pulled = false;
                buriedItem.gameObject.SetActive(false);
                return false;
            }

            item = buriedItem;
            GameManager.Instance?.ShowMessage("Pulled an item from the ground!", 1.2f);
            Destroy(gameObject);
            return true;
        }
    }
}
