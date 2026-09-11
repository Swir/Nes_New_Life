using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(BoxCollider2D))]
    public sealed class CameraZone : MonoBehaviour
    {
        [SerializeField] private Vector2 worldCenter;
        [SerializeField] private Vector2 worldSize = new Vector2(18f, 10f);

        private void Reset()
        {
            BoxCollider2D collider = GetComponent<BoxCollider2D>();
            collider.isTrigger = true;
            worldCenter = transform.position;
            worldSize = collider.size;
        }

        public void Configure(Vector2 center, Vector2 size)
        {
            worldCenter = center;
            worldSize = new Vector2(Mathf.Max(1f, size.x), Mathf.Max(1f, size.y));

            BoxCollider2D collider = GetComponent<BoxCollider2D>();
            collider.isTrigger = true;
            collider.offset = transform.InverseTransformPoint(center);
            collider.size = worldSize;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (other.GetComponentInParent<PlayerController2D>() == null)
                return;

            Camera camera = Camera.main;
            if (camera == null)
                return;

            CameraFollow2D follow = camera.GetComponent<CameraFollow2D>();
            if (follow == null)
                return;

            Rect bounds = new Rect(
                worldCenter.x - worldSize.x * 0.5f,
                worldCenter.y - worldSize.y * 0.5f,
                worldSize.x,
                worldSize.y
            );
            follow.SetWorldBounds(bounds);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.DrawWireCube(worldCenter, worldSize);
        }
    }
}
