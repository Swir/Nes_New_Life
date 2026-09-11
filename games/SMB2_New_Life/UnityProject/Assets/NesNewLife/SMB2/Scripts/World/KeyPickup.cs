using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    public sealed class KeyPickup : MonoBehaviour
    {
        private void Reset()
        {
            Collider2D collider = GetComponent<Collider2D>();
            if (collider != null)
                collider.isTrigger = true;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerInventory inventory = other.GetComponentInParent<PlayerInventory>();
            if (inventory == null)
                return;

            inventory.AddKey();
            Destroy(gameObject);
        }
    }
}
