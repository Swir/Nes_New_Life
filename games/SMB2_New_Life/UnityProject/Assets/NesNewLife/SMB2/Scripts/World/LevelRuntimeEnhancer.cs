using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class LevelRuntimeEnhancer : MonoBehaviour
    {
        private const int GroundLayer = 8;

        private void Start()
        {
            if (GameObject.Find("V04_RUNTIME_ENCOUNTERS") != null)
                return;

            PlayerController2D player = FindFirstObjectByType<PlayerController2D>();
            if (player == null)
                return;

            SpriteRenderer sourceRenderer = player.GetComponent<SpriteRenderer>();
            Sprite sprite = sourceRenderer != null ? sourceRenderer.sprite : null;
            if (sprite == null)
                return;

            GameObject root = new GameObject("V04_RUNTIME_ENCOUNTERS");
            CreateHopper(root.transform, new Vector2(-3f, -1.25f), sprite);
            CreateChaser(root.transform, new Vector2(32f, -1.25f), 30f, 36f, sprite);
            CreateHopper(root.transform, new Vector2(20f, -19.2f), sprite);

            if (CampaignSave.Clears >= 1)
                CreateChaser(root.transform, new Vector2(46f, -1.25f), 42f, 51f, sprite);
        }

        private static void CreateHopper(Transform parent, Vector2 position, Sprite sprite)
        {
            GameObject enemy = CreateEnemyBase("Enemy_Hopper", parent, position, new Color(0.96f, 0.48f, 0.18f), sprite);
            EnemyHopper hopper = enemy.AddComponent<EnemyHopper>();
            hopper.Configure(8.8f, 2.4f, 1.25f, 1 << GroundLayer);
        }

        private static void CreateChaser(Transform parent, Vector2 position, float left, float right, Sprite sprite)
        {
            GameObject enemy = CreateEnemyBase("Enemy_Chaser", parent, position, new Color(0.92f, 0.18f, 0.42f), sprite);
            EnemyChaser chaser = enemy.AddComponent<EnemyChaser>();
            chaser.Configure(left, right, 1.3f, 3.4f, 7.5f);
        }

        private static GameObject CreateEnemyBase(string name, Transform parent, Vector2 position, Color color, Sprite sprite)
        {
            GameObject enemy = new GameObject(name);
            enemy.transform.SetParent(parent);
            enemy.transform.position = position;
            enemy.transform.localScale = new Vector3(0.9f, 0.9f, 1f);

            SpriteRenderer renderer = enemy.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;

            Rigidbody2D body = enemy.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            enemy.AddComponent<BoxCollider2D>();

            EnemyHealth health = enemy.AddComponent<EnemyHealth>();
            health.Configure(1, 400);
            enemy.AddComponent<DamageOnContact>();
            return enemy;
        }
    }
}
