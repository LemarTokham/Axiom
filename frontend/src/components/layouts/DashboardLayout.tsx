import Navbar from "@/components/pages/DashboardLayout/Navbar.tsx";
import Footer from "@/components/pages/DashboardLayout/Footer.tsx";
import {Outlet} from "react-router";



function DashboardLayout() {
    return (
        <div className="flex flex-col h-screen">
            <Navbar/>
            <main className="flex-1 flex flex-col">
                <Outlet/>
            </main>
            <Footer/>
        </div>
    );
}

export default DashboardLayout;