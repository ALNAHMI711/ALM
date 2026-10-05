using System.Collections.Generic;
using UnityEngine;

namespace YOW.Content
{
    public sealed class OfflinePackRegistry : MonoBehaviour
    {
        private readonly HashSet<string> installed = new();

        public bool IsInstalled(string packId) => installed.Contains(packId);

        public void MarkInstalled(string packId)
        {
            if (!string.IsNullOrWhiteSpace(packId))
                installed.Add(packId);
        }

        public void Remove(string packId) => installed.Remove(packId);
    }
}
