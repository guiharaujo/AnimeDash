FETCH_TOP_ANIMES_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(
      type: ANIME
      sort: POPULARITY_DESC
      isAdult: false
    ) {
      id
      title {
        romaji
        native
      }
      genres
      meanScore
      popularity
      episodes
      status
      season
      seasonYear
      studios(isMain: true) {
        nodes {
          name
        }
      }
      description(asHtml: false)
      coverImage {
        large
      }
      tags {
        id
        name
        description
        rank
      }
    }
  }
}
"""
