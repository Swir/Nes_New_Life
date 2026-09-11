using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class KillZone : MonoBehaviour
    {
        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerHealth player = other.GetComponentInParent<PlayerHealth>();
            if (player != null && GameManager.Instance != null)
                GameManager.Instance.PlayerDied();
        }
    }
}
