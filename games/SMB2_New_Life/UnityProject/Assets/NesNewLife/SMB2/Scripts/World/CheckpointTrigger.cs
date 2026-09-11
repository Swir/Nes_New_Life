using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class CheckpointTrigger : MonoBehaviour
    {
        [SerializeField] private Vector3 respawnOffset = new Vector3(0f, 1f, 0f);
        private bool activated;

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (activated || other.GetComponentInParent<PlayerController2D>() == null || GameManager.Instance == null)
                return;

            activated = true;
            GameManager.Instance.SetCheckpoint(transform.position + respawnOffset);

            SpriteRenderer renderer = GetComponent<SpriteRenderer>();
            if (renderer != null)
                renderer.color = new Color(0.25f, 1f, 0.55f);
        }
    }
}
