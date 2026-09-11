using System.Collections;
using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    [RequireComponent(typeof(SpriteRenderer))]
    public sealed class CrumblePlatform2D : MonoBehaviour
    {
        [SerializeField, Min(0.05f)] private float crumbleDelay = 0.55f;
        [SerializeField, Min(0.1f)] private float respawnDelay = 2.5f;

        private Collider2D platformCollider;
        private SpriteRenderer spriteRenderer;
        private Coroutine routine;

        private void Awake()
        {
            platformCollider = GetComponent<Collider2D>();
            spriteRenderer = GetComponent<SpriteRenderer>();
        }

        private void OnCollisionEnter2D(Collision2D collision)
        {
            if (routine != null || collision.collider.GetComponentInParent<PlayerController2D>() == null)
                return;

            routine = StartCoroutine(CrumbleRoutine());
        }

        private IEnumerator CrumbleRoutine()
        {
            float elapsed = 0f;
            Color original = spriteRenderer.color;
            while (elapsed < crumbleDelay)
            {
                elapsed += 0.08f;
                spriteRenderer.color = Color.Lerp(original, new Color(1f, 0.45f, 0.2f, 1f), elapsed / crumbleDelay);
                yield return new WaitForSeconds(0.08f);
            }

            platformCollider.enabled = false;
            spriteRenderer.enabled = false;
            yield return new WaitForSeconds(respawnDelay);
            spriteRenderer.color = original;
            spriteRenderer.enabled = true;
            platformCollider.enabled = true;
            routine = null;
        }
    }
}
