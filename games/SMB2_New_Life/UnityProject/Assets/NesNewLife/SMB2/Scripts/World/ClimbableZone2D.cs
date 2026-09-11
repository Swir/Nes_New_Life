using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Collider2D))]
    public sealed class ClimbableZone2D : MonoBehaviour
    {
        private void Reset()
        {
            Collider2D zone = GetComponent<Collider2D>();
            zone.isTrigger = true;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            PlayerController2D player = other.GetComponentInParent<PlayerController2D>();
            if (player != null)
                player.SetClimbableContact(true);
        }

        private void OnTriggerExit2D(Collider2D other)
        {
            PlayerController2D player = other.GetComponentInParent<PlayerController2D>();
            if (player != null)
                player.SetClimbableContact(false);
        }
    }
}
