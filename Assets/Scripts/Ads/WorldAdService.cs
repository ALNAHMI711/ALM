using System.Collections.Generic;
using UnityEngine;

namespace YOW.Ads
{
    public sealed class WorldAdService : MonoBehaviour
    {
        public IReadOnlyList<WorldAdDefinition> ActiveAds => activeAds;
        private readonly List<WorldAdDefinition> activeAds = new();

        public void ReplaceAds(IEnumerable<WorldAdDefinition> ads)
        {
            activeAds.Clear();
            if (ads == null) return;
            foreach (var ad in ads)
                if (ad != null && ad.enabled)
                    activeAds.Add(ad);
        }

        public WorldAdDefinition GetForPlacement(string placementId)
        {
            foreach (var ad in activeAds)
                if (ad.placementId == placementId)
                    return ad;
            return null;
        }
    }
}
