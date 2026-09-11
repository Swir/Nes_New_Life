using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class HeartPickup : MonoBehaviour
    {
        [SerializeField, Min(1)] private int healAmount = 1;
        [SerializeField, Min(0)] private int score = 100;

        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerHealth health = other.GetComponentInParent<PlayerHealth>();
            if (health == null)
                return;

            health.Heal(healAmount);
            if (GameManager.Instance != null)
                GameManager.Instance.AddScore(score);
            Destroy(gameObject);
        }
    }
}
