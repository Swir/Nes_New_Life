using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class PlayerInventory : MonoBehaviour
    {
        [SerializeField, Min(0)] private int keys;

        public int Keys => keys;

        public void AddKey(int amount = 1)
        {
            keys = Mathf.Max(0, keys + Mathf.Max(0, amount));
            GameManager.Instance?.ShowMessage($"Key acquired  •  Keys: {keys}", 1.8f);
        }

        public bool TryConsumeKey()
        {
            if (keys <= 0)
                return false;

            keys--;
            GameManager.Instance?.ShowMessage($"Door unlocked  •  Keys: {keys}", 1.6f);
            return true;
        }

        public void ClearKeys()
        {
            keys = 0;
        }
    }
}
