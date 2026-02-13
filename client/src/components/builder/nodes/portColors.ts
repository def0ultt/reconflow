import { PortType } from '../../../types';

export const PORT_COLORS: Record<PortType, string> = {
    string: '#a855f7', // purple
    boolean: '#3b82f6', // blue
    file: '#f97316', // orange
    folder: '#22c55e', // green
};

export const PORT_LABELS: Record<PortType, string> = {
    string: 'String',
    boolean: 'Boolean',
    file: 'File',
    folder: 'Folder',
};

export const portColorClass = (type: PortType) => {
    const map: Record<PortType, string> = {
        string: 'port-string',
        boolean: 'port-boolean',
        file: 'port-file',
        folder: 'port-folder',
    };
    return map[type] || 'port-string';
};
