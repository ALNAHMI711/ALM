using System.Collections.Generic;
using UnityEngine;

namespace YOW.Map
{
    public sealed class MapDirectory : MonoBehaviour
    {
        [SerializeField] private List<MapLocationDefinition> locations = new();

        public IReadOnlyList<MapLocationDefinition> Locations => locations;

        public IEnumerable<MapLocationDefinition> FindByCategory(LocationCategory category)
        {
            foreach (var location in locations)
                if (location.category == category)
                    yield return location;
        }
    }
}
