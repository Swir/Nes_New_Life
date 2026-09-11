using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class EnemyHealth : MonoBehaviour
    {
        [SerializeField, Min(1)] private int maxHealth = 1;
        [SerializeField, Min(0)] private int scoreReward = 250;

        private int currentHealth;
        public bool IsDead { get; private set; }

        private void Awake()
        {
            currentHealth = maxHealth;
        }

        public void Damage(int amount)
        {
            if (IsDead || amount <= 0)
                return;

            currentHealth -= amount;
            if (currentHealth > 0)
                return;

            IsDead = true;
            if (GameManager.Instance != null)
                GameManager.Instance.AddScore(scoreReward);

            Destroy(gameObject);
        }
    }
}
