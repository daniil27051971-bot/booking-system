import { useEffect, useState } from "react"

import { getMyBookings, cancelBooking } from "../api/bookingsApi"
import { getResources } from "../api/resourcesApi"
import "../styles/myBookings.css"

function MyBookings() {
    const [bookings, setBookings] = useState([])
    const [resources, setResources] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        try {
            const bookingsData = await getMyBookings()
            const resourcesData = await getResources()

            setBookings(bookingsData)
            setResources(resourcesData)
        } catch (error) {
            console.log(error)
            alert("Ошибка загрузки бронирований")
        } finally {
            setLoading(false)
        }
    }

    function getResourceName(resourceId) {
        const resource = resources.find(item => item.id === resourceId)
        return resource ? resource.name : `Ресурс ID: ${resourceId}`
    }

    function formatDate(datetime) {
        return new Date(datetime).toLocaleDateString("ru-RU")
    }

    function formatTime(datetime) {
        return new Date(datetime).toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit"
        })
    }

    function isPastBooking(booking) {
        return new Date(booking.end_datetime) < new Date()
    }

    function getStatusText(booking) {
        if (booking.status === "cancelled") return "Отменена"
        if (isPastBooking(booking)) return "Завершена"
        if (booking.status === "confirmed") return "Активна"

        return booking.status
    }

    async function handleCancel(id) {
        const confirmCancel = window.confirm("Точно отменить бронь?")

        if (!confirmCancel) return

        try {
            await cancelBooking(id)
            alert("Бронь отменена")
            await loadData()
        } catch (error) {
            console.log(error)
            alert(error.response?.data?.detail || "Ошибка отмены брони")
        }
    }

    const activeBookings = bookings.filter(booking => {
        return booking.status === "confirmed" && !isPastBooking(booking)
    })

    const oldBookings = bookings.filter(booking => {
        return booking.status !== "confirmed" || isPastBooking(booking)
    })

    if (loading) {
        return (
            <div className="bookings-page">
                <h1>Мои бронирования</h1>
                <p>Загрузка...</p>
            </div>
        )
    }

    return (
        <div className="bookings-page">
            <h1>Мои бронирования</h1>

            <section className="bookings-section">
                <h2>Активные бронирования</h2>

                {activeBookings.length === 0 && (
                    <p className="empty-text">У вас нет активных бронирований</p>
                )}

                <div className="bookings-list">
                    {activeBookings.map(booking => (
                        <div key={booking.id} className="booking-card">
                            <div className="booking-card-header">
                                <h3>{getResourceName(booking.resource_id)}</h3>

                                <span className="booking-status active">
                                    {getStatusText(booking)}
                                </span>
                            </div>

                            <p>Дата: <span>{formatDate(booking.start_datetime)}</span></p>

                            <p>
                                Время:{" "}
                                <span>
                                    {formatTime(booking.start_datetime)} – {formatTime(booking.end_datetime)}
                                </span>
                            </p>

                            <p>Цель: <span>{booking.purpose || "Не указана"}</span></p>

                            <button
                                className="cancel-btn"
                                onClick={() => handleCancel(booking.id)}
                            >
                                Отменить
                            </button>
                        </div>
                    ))}
                </div>
            </section>

            <section className="bookings-section">
                <h2>История бронирований</h2>

                {oldBookings.length === 0 && (
                    <p className="empty-text">История пока пустая</p>
                )}

                <div className="bookings-list">
                    {oldBookings.map(booking => (
                        <div key={booking.id} className="booking-card muted">
                            <div className="booking-card-header">
                                <h3>{getResourceName(booking.resource_id)}</h3>

                                <span className="booking-status old">
                                    {getStatusText(booking)}
                                </span>
                            </div>

                            <p>Дата: <span>{formatDate(booking.start_datetime)}</span></p>

                            <p>
                                Время:{" "}
                                <span>
                                    {formatTime(booking.start_datetime)} – {formatTime(booking.end_datetime)}
                                </span>
                            </p>

                            <p>Цель: <span>{booking.purpose || "Не указана"}</span></p>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    )
}

export default MyBookings