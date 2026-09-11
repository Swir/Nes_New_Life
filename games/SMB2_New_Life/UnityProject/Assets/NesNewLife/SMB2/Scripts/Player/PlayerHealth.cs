using System.Collections;
using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(SpriteRenderer))]
    public sealed class PlayerHealth : MonoBehaviour
    {
        [SerializeField, Min(1)] private int maxHealth = 3;
        [SerializeField, Min(0f)] private float invulnerabilitySeconds = 1.2f;
        [SerializeField, Min(0f)] private float knockbackHorizontal = 4f;
        [SerializeField, Min(0f)] private float knockbackVertical = 5f;

        private int currentHealth;
        private bool invulnerable;
        private SpriteRenderer spriteRenderer;
        private Rigidbody2D body;

        public int CurrentHealth => currentHealth;
        public int MaxHealth => maxHealth;
        public bool IsInvulnerable => invulnerable;

        private void Awake()
        {
            currentHealth = maxHealth;
            spriteRenderer = GetComponent<SpriteRenderer>();
            body = GetComponent<Rigidbody2D>();
        }

        public void Damage(int amount, Vector2 sourcePosition)
        {
            if (amount <= 0 || invulnerable || GameManager.Instance == null || GameManager.Instance.State != RunState.Playing)
                return;

            currentHealth -= amount;
            if (currentHealth <= 0)
            {
                currentHealth = 0;
                GameManager.Instance.PlayerDied();
                return;
            }

            if (body != null)
            {
                float sign = transform.position.x >= sourcePosition.x ? 1f : -1f;
                body.linearVelocity = new Vector2(sign * knockbackHorizontal, knockbackVertical);
            }

            StartCoroutine(InvulnerabilityRoutine());
        }

        public void Heal(int amount)
        {
            if (amount <= 0)
                return;
            currentHealth = Mathf.Clamp(currentHealth + amount, 0, maxHealth);
        }

        public void RestoreFull()
        {
            StopAllCoroutines();
            invulnerable = false;
            currentHealth = maxHealth;
            if (spriteRenderer != null)
                spriteRenderer.enabled = true;
        }

        private IEnumerator InvulnerabilityRoutine()
        {
            invulnerable = true;
            float elapsed = 0f;
            while (elapsed < invulnerabilitySeconds)
            {
                spriteRenderer.enabled = !spriteRenderer.enabled;
                yield return new WaitForSeconds(0.08f);
                elapsed += 0.08f;
            }

            spriteRenderer.enabled = true;
            invulnerable = false;
        }
    }
}
