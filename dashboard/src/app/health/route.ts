import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        status: 'healthy',
        app: 'ContractorVault Dashboard',
        version: '1.0.0'
    });
}
