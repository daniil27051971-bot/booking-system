import api from "./axios"

export async function createBooking(data) {
    const response = await api.post("/bookings/", data)
    return response.data
}

export async function getMyBookings() {
    const response = await api.get("/bookings/")
    return response.data
}

export async function cancelBooking(id) {
    const response = await api.delete(`/bookings/${id}`)
    return response.data
}

export async function getResourceScheduleGrid(resourceId, weekStart) {
    const response = await api.get(`/bookings/schedule/${resourceId}`, {
        params: {
            week_start: `${weekStart}T00:00:00`
        }
    })

    return response.data
}