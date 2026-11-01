using u64 = unsigned long long;
using u32 = unsigned int;
struct Group {
    void* source;
    u32 capacity;
    u32 count;
    void** items;
    float distance;
    u32 flags;
};
static_assert(sizeof(Group) == 32, "Native particle group layout");
extern "C" void Append(void* vector, void** item);

// Called once after the global sort and after all gather workers finish.
// Preserve the exact emitter sequence. Only consecutive same-source groups
// can join; another source or an empty entry ends the run.
extern "C" u64 MergeAdjacent(void* raw) {
    auto bytes = static_cast<unsigned char*>(raw);
    const u64 count = *reinterpret_cast<u64*>(bytes + 0x38);
    auto segments = *reinterpret_cast<unsigned char***>(bytes + 0x10);
    Group* head = nullptr;
    u64 runs = 0;
    u32 segment = 0;
    for (u64 i = 0; i < count; ++i) {
        if (i >= 2 && (i & (i - 1)) == 0) ++segment;
        auto current = reinterpret_cast<Group*>(segments[segment] + i * sizeof(Group));
        if (!current->source || !current->count) {
            head = nullptr;
            continue;
        }
        if (head && head->source == current->source) {
            for (u32 j = 0; j < current->count; ++j)
                Append(reinterpret_cast<unsigned char*>(head) + 8, &current->items[j]);
            // The native iterator skips null owners. Leave its vector intact
            // so the native concurrent-vector destructor still frees it.
            current->source = nullptr;
        } else {
            head = current;
            ++runs;
        }
    }
    return runs;
}
