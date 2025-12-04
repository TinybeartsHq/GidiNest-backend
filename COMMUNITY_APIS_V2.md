# Community APIs - V2 Complete Reference

**Status:** ✅ **FULLY IMPLEMENTED**
**Total Endpoints:** 19
**Base URL:** `/api/v2/community/`

---

## 📊 API Overview

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Community Stats** | 1 | Overall community statistics |
| **Groups** | 3 | Group management and membership |
| **Posts** | 3 | Post creation, viewing, and interactions |
| **Comments** | 2 | Comment on posts |
| **Moderation** | 4 | Content moderation (Admin/Moderator) |
| **Challenges** | 3 | Savings challenges and participation |
| **Leaderboard** | 1 | Group leaderboard rankings |

---

## 1️⃣ COMMUNITY STATS

### Get Community Statistics
**Endpoint:** `GET /api/v2/community/stats`
**Auth:** Required
**Permission:** IsAuthenticated

**Response:**
```json
{
  "success": true,
  "data": {
    "total_groups": 10,
    "total_posts": 250,
    "total_members": 500,
    "active_challenges": 5,
    "my_groups_count": 3,
    "my_posts_count": 15,
    "my_challenges_count": 2
  }
}
```

**Use Case:** Dashboard overview, analytics

---

## 2️⃣ GROUPS

### 2.1 List/Create Groups
**Endpoint:** `GET/POST /api/v2/community/groups`
**Auth:** Required
**Permission:** IsAuthenticated

#### GET - List Groups
**Query Parameters:**
- `category` (optional): Filter by category (pregnancy, postpartum, ttc, general)
- `badge` (optional): Filter by badge (new_mom, experienced, verified)
- `search` (optional): Search by name or description

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "First Time Moms",
      "description": "Support group for first-time mothers",
      "category": "pregnancy",
      "badge": "new_mom",
      "privacy": "public",
      "member_count": 150,
      "post_count": 45,
      "is_member": true,
      "user_role": "member",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### POST - Create Group
**Request Body:**
```json
{
  "name": "Lagos Moms Network",
  "description": "Connect with moms in Lagos",
  "category": "general",
  "badge": "verified",
  "privacy": "public",
  "settings": {
    "require_approval": false,
    "allow_posts": true
  }
}
```

**Categories:** `pregnancy`, `postpartum`, `ttc` (trying to conceive), `general`
**Badges:** `new_mom`, `experienced`, `verified`, `champion`
**Privacy:** `public`, `private`

---

### 2.2 Group Details
**Endpoint:** `GET/PUT/DELETE /api/v2/community/groups/<group_id>`
**Auth:** Required

#### GET - View Group Details
**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "First Time Moms",
    "description": "Support group...",
    "category": "pregnancy",
    "privacy": "public",
    "member_count": 150,
    "post_count": 45,
    "is_member": true,
    "user_role": "admin",
    "recent_posts": [...],
    "top_members": [...],
    "settings": {
      "require_approval": false,
      "allow_posts": true
    }
  }
}
```

#### PUT - Update Group (Admin only)
**Request Body:** Same as create, partial updates allowed

#### DELETE - Delete Group (Admin only)
Soft deletes the group (sets `is_active=False`)

---

### 2.3 Join/Leave Group
**Endpoint:** `POST /api/v2/community/groups/<group_id>/join`
**Auth:** Required

**Request Body:**
```json
{
  "action": "join"  // or "leave"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully joined the group",
  "data": {
    "is_member": true,
    "role": "member",
    "member_count": 151
  }
}
```

**Notes:**
- Private groups may require admin approval
- Leaving a group removes membership

---

## 3️⃣ POSTS

### 3.1 List/Create Posts
**Endpoint:** `GET/POST /api/v2/community/posts`
**Auth:** Required

#### GET - List Posts
**Query Parameters:**
- `group` (optional): Filter by group ID
- `status` (optional): Filter by status (pending, approved, rejected)
- `ordering` (optional): Sort by field (e.g., `-created_at`, `likes_count`)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "group": {
        "id": 1,
        "name": "First Time Moms"
      },
      "author": {
        "id": "uuid",
        "first_name": "Jane",
        "last_name": "Doe",
        "badge": "new_mom"
      },
      "content": "Just had my first ultrasound!",
      "image": "https://...",
      "status": "approved",
      "likes_count": 25,
      "comments_count": 10,
      "views_count": 150,
      "is_liked": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### POST - Create Post
**Request Body:**
```json
{
  "group": 1,
  "content": "Just had my first ultrasound! So excited!",
  "image": "data:image/png;base64,..."  // optional
}
```

**Notes:**
- Posts may require moderation based on group settings
- Image uploads supported (base64 or multipart)

---

### 3.2 Post Details
**Endpoint:** `GET/PUT/DELETE /api/v2/community/posts/<post_id>`
**Auth:** Required

#### GET - View Post Details
Includes full post data with comments

#### PUT - Update Post (Author only)
**Request Body:** Same as create, partial updates allowed

#### DELETE - Delete Post (Author or Admin)
Soft deletes the post

---

### 3.3 Like/Unlike Post
**Endpoint:** `POST /api/v2/community/posts/<post_id>/like`
**Auth:** Required

**Request Body:**
```json
{
  "action": "like"  // or "unlike"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Post liked successfully",
  "data": {
    "is_liked": true,
    "likes_count": 26
  }
}
```

---

## 4️⃣ COMMENTS

### 4.1 List/Create Comments
**Endpoint:** `GET/POST /api/v2/community/posts/<post_id>/comments`
**Auth:** Required

#### GET - List Comments
**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "post": 1,
      "author": {
        "id": "uuid",
        "first_name": "Sarah",
        "badge": "experienced"
      },
      "content": "Congratulations! That's so exciting!",
      "status": "approved",
      "created_at": "2025-01-15T11:00:00Z"
    }
  ]
}
```

#### POST - Create Comment
**Request Body:**
```json
{
  "content": "Congratulations! That's wonderful news!"
}
```

---

### 4.2 Update/Delete Comment
**Endpoint:** `PUT/DELETE /api/v2/community/comments/<comment_id>`
**Auth:** Required
**Permission:** Author or Admin

**PUT Request:**
```json
{
  "content": "Updated comment text"
}
```

---

## 5️⃣ MODERATION (Admin/Moderator Only)

### 5.1 List Posts Pending Moderation
**Endpoint:** `GET /api/v2/community/moderation/posts`
**Auth:** Required
**Permission:** CanModerateContent

**Query Parameters:**
- `status` (optional): Filter by status (pending, approved, rejected)
- `group` (optional): Filter by group ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "group": {...},
      "author": {...},
      "content": "Post content...",
      "status": "pending",
      "moderation_notes": null,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

### 5.2 Approve/Reject Post
**Endpoint:** `POST /api/v2/community/moderation/posts/<post_id>/review`
**Auth:** Required
**Permission:** CanModerateContent

**Request Body:**
```json
{
  "action": "approve",  // or "reject"
  "moderation_notes": "Optional note about decision"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Post approved successfully",
  "data": {
    "status": "approved",
    "moderated_by": "admin@example.com",
    "moderated_at": "2025-01-15T12:00:00Z"
  }
}
```

---

### 5.3 List Comments Pending Moderation
**Endpoint:** `GET /api/v2/community/moderation/comments`
**Auth:** Required
**Permission:** CanModerateContent

Similar to post moderation list

---

### 5.4 Approve/Reject Comment
**Endpoint:** `POST /api/v2/community/moderation/comments/<comment_id>/review`
**Auth:** Required
**Permission:** CanModerateContent

Same as post review

---

## 6️⃣ CHALLENGES

### 6.1 List/Create Challenges
**Endpoint:** `GET/POST /api/v2/community/challenges`
**Auth:** Required

#### GET - List Challenges
**Query Parameters:**
- `status` (optional): Filter by status (upcoming, active, completed)
- `group` (optional): Filter by group ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "group": {...},
      "title": "Save ₦100,000 in 30 Days",
      "description": "Join us to save together!",
      "target_amount": "100000.00",
      "duration_days": 30,
      "start_date": "2025-02-01",
      "end_date": "2025-03-03",
      "status": "active",
      "participant_count": 45,
      "total_saved": "2500000.00",
      "is_participating": true,
      "my_progress": {
        "amount_saved": "75000.00",
        "progress_percentage": 75.0,
        "rank": 12
      }
    }
  ]
}
```

#### POST - Create Challenge (Group Admin)
**Request Body:**
```json
{
  "group": 1,
  "title": "February Savings Challenge",
  "description": "Let's save ₦100k together this month!",
  "target_amount": "100000.00",
  "duration_days": 30,
  "start_date": "2025-02-01",
  "rules": {
    "minimum_contribution": "1000.00",
    "allow_early_completion": true
  }
}
```

---

### 6.2 Join Challenge
**Endpoint:** `POST /api/v2/community/challenges/<challenge_id>/join`
**Auth:** Required

**Response:**
```json
{
  "success": true,
  "message": "Successfully joined the challenge",
  "data": {
    "participation_id": 123,
    "challenge_title": "Save ₦100,000 in 30 Days",
    "target_amount": "100000.00",
    "start_date": "2025-02-01",
    "end_date": "2025-03-03"
  }
}
```

---

### 6.3 Update Challenge Progress
**Endpoint:** `POST /api/v2/community/challenge-participations/<participation_id>/update-progress`
**Auth:** Required

**Request Body:**
```json
{
  "amount_saved": "50000.00"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Progress updated successfully",
  "data": {
    "amount_saved": "50000.00",
    "progress_percentage": 50.0,
    "is_completed": false,
    "rank": 15,
    "updated_at": "2025-02-15T10:00:00Z"
  }
}
```

---

## 7️⃣ LEADERBOARD

### Get Group Leaderboard
**Endpoint:** `GET /api/v2/community/groups/<group_id>/leaderboard`
**Auth:** Required

**Query Parameters:**
- `period` (optional): Time period (weekly, monthly, all_time) - default: monthly

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "monthly",
    "updated_at": "2025-01-15T12:00:00Z",
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "uuid",
          "first_name": "Sarah",
          "last_name": "J.",
          "badge": "champion"
        },
        "total_savings": "500000.00",
        "posts_count": 25,
        "contributions_count": 50,
        "points": 1250
      },
      {
        "rank": 2,
        "user": {...},
        "total_savings": "450000.00",
        "points": 1100
      }
    ],
    "my_rank": {
      "rank": 15,
      "total_savings": "200000.00",
      "points": 500
    }
  }
}
```

**Notes:**
- Leaderboard rankings based on savings, posts, and community engagement
- Rankings updated periodically (cached)

---

## 🔒 Permissions Summary

| Permission | Description | Applies To |
|------------|-------------|------------|
| `IsAuthenticated` | Must be logged in | All endpoints |
| `IsAuthorOrReadOnly` | Author can edit/delete | Posts, Comments |
| `IsGroupMemberOrReadOnly` | Members can post | Group content |
| `IsGroupAdminOrModerator` | Admin/Mod can manage | Group settings |
| `CanModerateContent` | Can moderate posts/comments | Moderation endpoints |

---

## 📱 Common Use Cases

### Use Case 1: Display Community Feed
```
1. GET /api/v2/community/posts?ordering=-created_at
2. For each post, show likes_count, comments_count
3. User can tap "Like" → POST /api/v2/community/posts/<id>/like
4. User can tap "Comment" → Navigate to POST /api/v2/community/posts/<id>/comments
```

### Use Case 2: Join and Participate in Challenge
```
1. GET /api/v2/community/challenges?status=active
2. User selects challenge → POST /api/v2/community/challenges/<id>/join
3. User saves money → POST /api/v2/community/challenge-participations/<id>/update-progress
4. View rankings → GET /api/v2/community/groups/<id>/leaderboard
```

### Use Case 3: Group Management
```
1. GET /api/v2/community/groups (discover groups)
2. User joins → POST /api/v2/community/groups/<id>/join
3. Create post → POST /api/v2/community/posts
4. View group feed → GET /api/v2/community/posts?group=<id>
```

---

## 🚀 Implementation Status

✅ All 19 endpoints fully implemented
✅ Permissions and access control configured
✅ Serializers with nested relationships
✅ Moderation workflow complete
✅ Leaderboard and statistics
✅ Challenge participation tracking

**File References:**
- Views: `community/views.py:1-744`
- URLs: `community/urls_v2.py:1-85`
- Models: `community/models.py`
- Serializers: `community/serializers.py`
- Permissions: `community/permissions.py`

---

## ⚠️ Notes for Frontend Integration

1. **Pagination:** Not yet implemented - all endpoints return full lists
   - TODO: Add pagination for posts, comments, groups

2. **Image Upload:** Currently supports base64 encoding
   - Consider implementing multipart/form-data for large images

3. **Real-time Updates:** Not implemented
   - Consider WebSocket integration for live notifications

4. **Caching:** No caching implemented
   - Leaderboard and stats should be cached for performance

5. **Rate Limiting:** Not configured
   - Should add rate limits to prevent spam posting

---

## 🧪 Testing Recommendations

- [ ] Test group privacy (public vs private access)
- [ ] Test moderation workflow (pending → approved/rejected)
- [ ] Test challenge participation and progress updates
- [ ] Test leaderboard calculations
- [ ] Test permissions (member vs admin vs moderator)
- [ ] Load test with multiple concurrent users
- [ ] Test image upload and storage

---

**Last Updated:** December 4, 2025
**Version:** V2.0
**Total Lines of Code:** 744 lines (views.py)
