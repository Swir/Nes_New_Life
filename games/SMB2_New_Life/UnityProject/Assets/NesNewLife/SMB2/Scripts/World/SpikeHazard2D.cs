using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    public sealed class SpikeHazard2D : MonoBehaviour
    {
        [SerializeField, Min(1)] private int damage = 1;

        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerHealth health = other.GetComponentInParent<PlayerHealth>();
            if (health != null)
                health.Damage(damage, transform.position);
        }

        private void OnTriggerStay2D(Collider2D other)
        {
            PlayerHealth health = other.GetComponentInParent<PlayerHealth>();
            if (health != null && !health.IsInvulnerable)
                health.Damage(damage, transform.position);
        }
    }
}
