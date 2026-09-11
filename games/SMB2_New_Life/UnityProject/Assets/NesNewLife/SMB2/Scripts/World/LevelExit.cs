using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class LevelExit : MonoBehaviour
    {
        private void OnTriggerEnter2D(Collider2D other)
        {
            if (other.GetComponentInParent<PlayerController2D>() == null || GameManager.Instance == null)
                return;

            if (FindFirstObjectByType<BossController>() != null)
            {
                GameManager.Instance.ShowMessage("Defeat the guardian first", 1.4f);
                return;
            }

            GameManager.Instance.CompleteCurrentStage();
        }
    }
}
