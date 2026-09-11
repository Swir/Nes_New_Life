using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class DamageOnContact : MonoBehaviour
    {
        [SerializeField, Min(1)] private int damage = 1;

        private void OnCollisionStay2D(Collision2D collision)
        {
            PlayerHealth player = collision.collider.GetComponentInParent<PlayerHealth>();
            if (player != null)
                player.Damage(damage, transform.position);
        }

        private void OnTriggerStay2D(Collider2D other)
        {
            PlayerHealth player = other.GetComponentInParent<PlayerHealth>();
            if (player != null)
                player.Damage(damage, transform.position);
        }
    }
}
