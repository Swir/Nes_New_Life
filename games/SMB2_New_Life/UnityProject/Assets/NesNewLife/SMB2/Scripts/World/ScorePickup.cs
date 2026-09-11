using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class ScorePickup : MonoBehaviour
    {
        [SerializeField, Min(1)] private int score = 100;

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (other.GetComponentInParent<PlayerController2D>() == null)
                return;

            if (GameManager.Instance != null)
                GameManager.Instance.AddScore(score);
            Destroy(gameObject);
        }
    }
}
