using System.Collections;
using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    public sealed class DoorPortal : MonoBehaviour
    {
        [SerializeField] private Transform destination;
        [SerializeField] private bool requiresKey;
        [SerializeField] private bool consumeKey = true;
        [SerializeField] private KeyCode enterKey = KeyCode.UpArrow;
        [SerializeField] private KeyCode alternateEnterKey = KeyCode.W;
        [SerializeField, Min(0.05f)] private float globalReentryCooldown = 0.65f;
        [SerializeField] private Vector2 destinationOffset = new Vector2(0f, 0.15f);

        private PlayerController2D nearbyPlayer;
        private static float globalCooldownUntil;
        private bool travelling;

        public bool RequiresKey => requiresKey;
        public Transform Destination => destination;

        private void Reset()
        {
            Collider2D collider = GetComponent<Collider2D>();
            if (collider != null)
                collider.isTrigger = true;
        }

        private void Update()
        {
            if (travelling || nearbyPlayer == null || destination == null)
                return;

            if (GameManager.Instance == null || GameManager.Instance.State != RunState.Playing)
                return;

            if (Time.unscaledTime < globalCooldownUntil)
                return;

            if (!Input.GetKeyDown(enterKey) && !Input.GetKeyDown(alternateEnterKey))
                return;

            PlayerInventory inventory = nearbyPlayer.GetComponent<PlayerInventory>();
            if (requiresKey)
            {
                if (inventory == null || inventory.Keys <= 0)
                {
                    GameManager.Instance.ShowMessage("Locked door — find a key", 1.8f);
                    return;
                }

                if (consumeKey && !inventory.TryConsumeKey())
                    return;
            }

            StartCoroutine(Travel(nearbyPlayer));
        }

        public void Configure(Transform target, bool keyRequired, bool shouldConsumeKey = true)
        {
            destination = target;
            requiresKey = keyRequired;
            consumeKey = shouldConsumeKey;
        }

        private IEnumerator Travel(PlayerController2D player)
        {
            travelling = true;
            globalCooldownUntil = Time.unscaledTime + globalReentryCooldown;

            Rigidbody2D body = player.GetComponent<Rigidbody2D>();
            if (body != null)
                body.linearVelocity = Vector2.zero;

            GameManager.Instance?.ShowMessage(requiresKey ? "Entering unlocked passage..." : "Entering...", 0.8f);
            yield return new WaitForSecondsRealtime(0.08f);

            player.transform.position = destination.position + (Vector3)destinationOffset;
            if (body != null)
                body.linearVelocity = Vector2.zero;

            yield return new WaitForSecondsRealtime(0.08f);
            travelling = false;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerController2D player = other.GetComponentInParent<PlayerController2D>();
            if (player == null)
                return;

            nearbyPlayer = player;
            if (GameManager.Instance != null)
                GameManager.Instance.ShowMessage(requiresKey ? "Press ↑ / W — locked door" : "Press ↑ / W — enter door", 1.2f);
        }

        private void OnTriggerExit2D(Collider2D other)
        {
            PlayerController2D player = other.GetComponentInParent<PlayerController2D>();
            if (player != null && player == nearbyPlayer)
                nearbyPlayer = null;
        }
    }
}
