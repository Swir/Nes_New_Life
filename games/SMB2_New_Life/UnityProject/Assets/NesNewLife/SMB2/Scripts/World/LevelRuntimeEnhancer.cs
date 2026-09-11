using UnityEngine;

namespace NesNewLife.SMB2
{
    public sealed class LevelRuntimeEnhancer : MonoBehaviour
    {
        private const int GroundLayer = 8;

        private void Start()
        {
            if (GameObject.Find("CAMPAIGN_RUNTIME_ENCOUNTERS") != null)
                return;

            PlayerController2D player = FindFirstObjectByType<PlayerController2D>();
            if (player == null)
                return;

            SpriteRenderer sourceRenderer = player.GetComponent<SpriteRenderer>();
            Sprite sprite = sourceRenderer != null ? sourceRenderer.sprite : null;
            if (sprite == null)
                return;

            CampaignStageDefinition stage = FindFirstObjectByType<CampaignStageDefinition>();
            int stageNumber = stage != null ? stage.StageNumber : 1;

            GameObject root = new GameObject("CAMPAIGN_RUNTIME_ENCOUNTERS");
            SpawnStageOne(root.transform, sprite);

            if (stageNumber >= 2)
                SpawnStageTwoPressure(root.transform, sprite);

            if (stageNumber >= 3)
                SpawnStageThreePressure(root.transform, sprite);

            if (CampaignSave.Clears >= 1)
                CreateChaser(root.transform, new Vector2(46f, -1.25f), 42f, 51f, 3.8f, sprite);
        }

        private static void SpawnStageOne(Transform root, Sprite sprite)
        {
            CreateHopper(root, new Vector2(-3f, -1.25f), 8.8f, 2.4f, 1.25f, sprite);
            CreateChaser(root, new Vector2(32f, -1.25f), 30f, 36f, 3.4f, sprite);
            CreateHopper(root, new Vector2(20f, -19.2f), 8.8f, 2.4f, 1.25f, sprite);
        }

        private static void SpawnStageTwoPressure(Transform root, Sprite sprite)
        {
            CreateHopper(root, new Vector2(7f, -1.25f), 9.6f, 2.9f, 1.05f, sprite);
            CreateChaser(root, new Vector2(22f, -1.25f), 18f, 26f, 3.8f, sprite);
            CreateHopper(root, new Vector2(12f, -19.2f), 9.8f, 2.8f, 1.0f, sprite);
        }

        private static void SpawnStageThreePressure(Transform root, Sprite sprite)
        {
            CreateChaser(root, new Vector2(-8f, -1.25f), -12f, -2f, 4.2f, sprite);
            CreateHopper(root, new Vector2(36f, -1.25f), 10.5f, 3.1f, 0.9f, sprite);
            CreateChaser(root, new Vector2(25f, -19.2f), 20f, 28f, 4.3f, sprite);
            CreateHopper(root, new Vector2(47f, -1.25f), 10.8f, 3.2f, 0.85f, sprite);
        }

        private static void CreateHopper(Transform parent, Vector2 position, float jumpVelocity, float horizontalSpeed, float interval, Sprite sprite)
        {
            GameObject enemy = CreateEnemyBase("Enemy_Hopper", parent, position, new Color(0.96f, 0.48f, 0.18f), sprite);
            EnemyHopper hopper = enemy.AddComponent<EnemyHopper>();
            hopper.Configure(jumpVelocity, horizontalSpeed, interval, 1 << GroundLayer);
        }

        private static void CreateChaser(Transform parent, Vector2 position, float left, float right, float chaseSpeed, Sprite sprite)
        {
            GameObject enemy = CreateEnemyBase("Enemy_Chaser", parent, position, new Color(0.92f, 0.18f, 0.42f), sprite);
            EnemyChaser chaser = enemy.AddComponent<EnemyChaser>();
            chaser.Configure(left, right, 1.3f, chaseSpeed, 7.5f);
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
